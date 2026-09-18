import React from "react";
import Dashboard from "./Dashboard";
import useScrollReveal from "./hooks/useScrollReveal";
import useScrollParallax from "./hooks/useScrollParallax";
import useSpotlight from "./hooks/useSpotlight";
import "./styles.css";

export default function App() {
  useScrollReveal();
  useScrollParallax();
  useSpotlight();
  return <Dashboard />;
}
