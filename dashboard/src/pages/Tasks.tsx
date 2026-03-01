import { PageWrapper } from "@/components/layout/PageWrapper";
import { TaskSubmitForm } from "@/components/tasks/TaskSubmitForm";
import { BatchSubmitButton } from "@/components/tasks/BatchSubmitButton";
import { TaskTable } from "@/components/tasks/TaskTable";

export function Tasks() {
  return (
    <PageWrapper
      title="Tasks"
      subtitle="Submit, monitor, and manage distributed tasks"
      actions={
        <div className="flex items-center gap-3">
          <BatchSubmitButton />
          <TaskSubmitForm />
        </div>
      }
    >
      <TaskTable />
    </PageWrapper>
  );
}
