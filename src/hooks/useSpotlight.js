import { useEffect } from "react";

// Single delegated pointermove listener for every [data-spotlight] card.
// Writes --sx/--sy (percent within the element) so the card's own
// ::after radial-gradient (see styles.css) can track the cursor. One
// listener for the whole page instead of one per card.
export default function useSpotlight() {
  useEffect(() => {
    if (window.matchMedia && window.matchMedia("(hover: none)").matches) return undefined;

    const handleMove = (e) => {
      const el = e.target.closest("[data-spotlight]");
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      el.style.setProperty("--sx", `${x}%`);
      el.style.setProperty("--sy", `${y}%`);
    };

    document.addEventListener("pointermove", handleMove);
    return () => document.removeEventListener("pointermove", handleMove);
  }, []);
}
