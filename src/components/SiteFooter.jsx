import React from "react";

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-inner">
        <div className="site-footer-brand">
          <img className="brand-mark" src="/praman-logo.jpeg" alt="Praman" />
          <div>
            <strong>Praman</strong>
            <p>
              Civic complaint intelligence. Named for the Sanskrit word for proof — because a
              dashboard that cannot show its evidence is just an opinion with charts.
            </p>
          </div>
        </div>

        <div className="site-footer-cols">
          <div>
            <h4>Product</h4>
            <a href="#what">What it does</a>
            <a href="#how">How it works</a>
            <a href="#board">Live board</a>
          </div>
          <div>
            <h4>Severity</h4>
            <span>Normal</span>
            <span>Emerging</span>
            <span>High Pressure</span>
          </div>
        </div>
      </div>
      <div className="site-footer-base">
        <span>© {new Date().getFullYear()} Praman</span>
        <span>Map data © OpenStreetMap contributors</span>
      </div>
    </footer>
  );
}
