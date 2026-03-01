import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { cancelTask, createTask, fetchTasks } from "@/api/tasks";
import type { TaskCreate } from "@/types/task";
import toast from "react-hot-toast";

export function useTasks(params?: {
  state?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
}) {
  return useQuery({
    queryKey: ["tasks", params],
    queryFn: () => fetchTasks(params),
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TaskCreate) => createTask(data),
    onSuccess: (task) => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success(`Task "${task.name}" created`);
    },
    onError: (err) => {
      toast.error(`Failed to create task: ${err.message}`);
    },
  });
}

export function useCancelTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (taskId: string) => cancelTask(taskId),
    onSuccess: (task) => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success(`Task "${task.name}" cancelled`);
    },
    onError: (err) => {
      toast.error(`Failed to cancel task: ${err.message}`);
    },
  });
}
