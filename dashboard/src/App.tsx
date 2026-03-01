import { Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { Overview } from "@/pages/Overview";
import { Tasks } from "@/pages/Tasks";
import { Workers } from "@/pages/Workers";
import { Metrics } from "@/pages/Metrics";
import { Events } from "@/pages/Events";
import { useRealtimeData } from "@/hooks/useRealtimeData";

export default function App() {
  useRealtimeData();

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/workers" element={<Workers />} />
            <Route path="/metrics" element={<Metrics />} />
            <Route path="/events" element={<Events />} />
          </Routes>
        </main>
      </div>
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: "#1e293b",
            color: "#e2e8f0",
            border: "1px solid #334155",
            fontSize: "13px",
          },
        }}
      />
    </div>
  );
}
