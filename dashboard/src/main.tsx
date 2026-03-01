import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { QueryProvider } from "./providers/QueryProvider";
import { WebSocketProvider } from "./providers/WebSocketProvider";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryProvider>
        <WebSocketProvider>
          <App />
        </WebSocketProvider>
      </QueryProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
