import React from "react";
import ReactDOM from "react-dom/client";
import "./theme.css";
import "./index.css";
import "./dark-theme.css";
import App from "./App.jsx";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
