import asyncio
import json
import time

import structlog

from chronos.config.constants import ETCD_ELECTION_KEY, ETCD_KEEPALIVE_INTERVAL, ETCD_LEASE_TTL

logger = structlog.get_logger(__name__)


class LeaderElection:
    """Leader election using etcd3 leases.

    Uses a simple put-if-absent pattern: the first node to write
    the election key with a lease becomes the leader. If the leader
    fails to renew the lease, the key expires and another node wins.
    """

    def __init__(self, etcd_client: object, node_id: str):
        self._client = etcd_client
        self._node_id = node_id
        self._is_leader = False
        self._lease = None
        self._running = False
        self._keepalive_task: asyncio.Task | None = None  # type: ignore[type-arg]

    @property
    def is_leader(self) -> bool:
        return self._is_leader

    @property
    def node_id(self) -> str:
        return self._node_id

    async def campaign(self) -> None:
        """Run the leader election campaign loop. Blocks indefinitely."""
        self._running = True
        while self._running:
            try:
                await self._try_acquire_leadership()
            except asyncio.CancelledError:
                self._running = False
                return
            except Exception as e:
                logger.error("leader_election_error", error=str(e), node_id=self._node_id)
                self._is_leader = False
                await asyncio.sleep(5)

    def _get_key_value(self, key: str) -> bytes | None:
        """Get a key's value from etcd. Returns None if not found."""
        try:
            result = self._client.range(key)
            if result.kvs:
                return result.kvs[0].value
        except Exception:
            pass
        return None

    async def _try_acquire_leadership(self) -> None:
        value = json.dumps({"node_id": self._node_id, "timestamp": time.time()})

        try:
            # Create and grant a lease
            self._lease = self._client.Lease(ttl=ETCD_LEASE_TTL)
            self._lease.grant()

            # Check if election key exists
            existing = self._get_key_value(ETCD_ELECTION_KEY)

            if existing is None:
                # No leader — try to become one
                self._client.put(ETCD_ELECTION_KEY, value, lease=self._lease.ID)
                self._is_leader = True
                logger.info("leader_elected", node_id=self._node_id)
                self._keepalive_task = asyncio.create_task(self._keepalive_loop())
                await self._hold_leadership()
            else:
                # Someone else is leader
                self._is_leader = False
                try:
                    if isinstance(existing, bytes):
                        existing = existing.decode()
                    leader_data = json.loads(existing)
                    logger.info(
                        "follower_mode",
                        node_id=self._node_id,
                        current_leader=leader_data.get("node_id"),
                    )
                except (json.JSONDecodeError, AttributeError):
                    logger.info("follower_mode", node_id=self._node_id)
                await self._wait_for_leader_loss()

        except Exception:
            self._is_leader = False
            raise

    async def _keepalive_loop(self) -> None:
        while self._is_leader and self._running:
            try:
                if self._lease:
                    self._lease.refresh()
            except Exception as e:
                logger.error("lease_refresh_failed", error=str(e))
                self._is_leader = False
                return
            await asyncio.sleep(ETCD_KEEPALIVE_INTERVAL)

    async def _hold_leadership(self) -> None:
        """Hold leadership until we lose it or stop."""
        while self._is_leader and self._running:
            await asyncio.sleep(1)

    async def _wait_for_leader_loss(self) -> None:
        """Wait until the current leader's key is gone, then retry."""
        while self._running:
            existing = self._get_key_value(ETCD_ELECTION_KEY)
            if existing is None:
                logger.info("leader_key_gone", node_id=self._node_id)
                return
            await asyncio.sleep(2)

    async def resign(self) -> None:
        """Voluntarily resign leadership."""
        self._running = False
        self._is_leader = False
        if self._keepalive_task:
            self._keepalive_task.cancel()
        try:
            self._client.delete_range(ETCD_ELECTION_KEY)
        except Exception:
            pass
        if self._lease:
            try:
                self._lease.revoke()
            except Exception:
                pass
        logger.info("leader_resigned", node_id=self._node_id)

    def get_leader(self) -> str | None:
        try:
            data = self._get_key_value(ETCD_ELECTION_KEY)
            if data:
                if isinstance(data, bytes):
                    data = data.decode()
                return json.loads(data).get("node_id")
        except Exception:
            pass
        return None
