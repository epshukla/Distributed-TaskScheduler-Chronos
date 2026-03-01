import { AnimatePresence } from "framer-motion";
import { useWorkers } from "@/hooks/useWorkers";
import { WorkerCard } from "./WorkerCard";
import { CardSkeleton } from "@/components/common/SkeletonLoader";

interface WorkerGridProps {
  statusFilter?: string;
}

export function WorkerGrid({ statusFilter }: WorkerGridProps) {
  const { data: workers, isLoading } = useWorkers(statusFilter);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (!workers || workers.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-gray-600">
        No workers registered
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      <AnimatePresence mode="popLayout">
        {workers.map((worker) => (
          <WorkerCard key={worker.id} worker={worker} />
        ))}
      </AnimatePresence>
    </div>
  );
}
