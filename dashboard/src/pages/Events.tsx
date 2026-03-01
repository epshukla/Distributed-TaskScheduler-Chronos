import { PageWrapper } from "@/components/layout/PageWrapper";
import { EventLog } from "@/components/events/EventLog";

export function Events() {
  return (
    <PageWrapper title="Events" subtitle="Real-time system event stream">
      <EventLog />
    </PageWrapper>
  );
}
