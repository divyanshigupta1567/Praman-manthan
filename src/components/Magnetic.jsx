import React, { useRef } from "react";

// Wraps a button/link so it drifts a few px toward the cursor while
// hovered and springs back on leave. Pointer-only effect; touch devices
// never fire mousemove here so nothing changes for them.
export default function Magnetic({ as: Tag = "button", className = "", children, strength = 14, ...rest }) {
  const ref = useRef(null);

  const handleMove = (e) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const relX = e.clientX - rect.left - rect.width / 2;
    const relY = e.clientY - rect.top - rect.height / 2;
    el.style.transform = `translate(${(relX / rect.width) * strength}px, ${(relY / rect.height) * strength}px)`;
  };

  const handleLeave = () => {
    if (ref.current) ref.current.style.transform = "";
  };

  return (
    <Tag ref={ref} className={`magnetic ${className}`} onMouseMove={handleMove} onMouseLeave={handleLeave} {...rest}>
      {children}
    </Tag>
  );
}
