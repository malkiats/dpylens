import React from "react";
import ReactDOM from "react-dom/client";
import "./styles.css";
import { LandingPage } from "./pages/LandingPage";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <LandingPage />
  </React.StrictMode>
);