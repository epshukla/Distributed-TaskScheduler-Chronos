import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ListTodo,
  Server,
  BarChart3,
  Activity,
  ChevronLeft,
  ChevronRight,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Overview" },
  { to: "/tasks", icon: ListTodo, label: "Tasks" },
  { to: "/workers", icon: Server, label: "Workers" },
  { to: "/metrics", icon: BarChart3, label: "Metrics" },
  { to: "/events", icon: Activity, label: "Events" },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { isConnected } = useWebSocket();

  return (
    <aside
      className={`flex h-screen flex-col border-r border-surface-100/20 bg-surface transition-all duration-200 ${
        collapsed ? "w-16" : "w-56"
      }`}
    >
      <div className="flex items-center gap-2 border-b border-surface-100/20 p-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent text-sm font-bold text-white">
          C
        </div>
        {!collapsed && (
          <span className="text-gradient text-lg font-bold">Chronos</span>
        )}
      </div>

      <nav className="flex-1 space-y-1 p-2">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                isActive
                  ? "bg-accent/10 text-accent-light"
                  : "text-gray-400 hover:bg-surface-50 hover:text-gray-200"
              }`
            }
          >
            <Icon size={18} />
            {!collapsed && label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-surface-100/20 p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isConnected ? (
              <Wifi size={14} className="text-emerald-400" />
            ) : (
              <WifiOff size={14} className="text-red-400" />
            )}
            {!collapsed && (
              <span
                className={`text-xs ${isConnected ? "text-emerald-400" : "text-red-400"}`}
              >
                {isConnected ? "Live" : "Disconnected"}
              </span>
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="rounded p-1 text-gray-500 hover:bg-surface-50 hover:text-gray-300"
          >
            {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
        </div>
      </div>
    </aside>
  );
}
