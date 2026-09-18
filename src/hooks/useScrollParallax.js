import { useEffect } from "react";

// Writes the current scroll position to --scrollY on the root element,
// rAF-throttled. CSS reads it (e.g. `calc(var(--scrollY) * 0.06px)`) to
// drift decorative layers as the page scrolls, without a scroll listener
// per element.
export default function useScrollParallax() {
  useEffect(() => {
    let ticking = false;
    const write = () => {
      document.documentElement.style.setProperty("--scrollY", String(window.scrollY));
      ticking = false;
    };
    const onScroll = () => {
      if (!ticking) {
        requestAnimationFrame(write);
        ticking = true;
      }
    };
    write();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
}
