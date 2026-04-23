import React, { useEffect, useState, useRef } from 'react';

/**
 * AnimatedCounter — Animates a number from 0 to `end` over `duration` ms.
 * Uses requestAnimationFrame for smooth 60fps animation.
 */
const AnimatedCounter = ({ end, duration = 1200, decimals = 1, prefix = '', suffix = '' }) => {
  const [value, setValue] = useState(0);
  const ref = useRef(null);
  const startTime = useRef(null);

  useEffect(() => {
    const target = parseFloat(end) || 0;

    const animate = (timestamp) => {
      if (!startTime.current) startTime.current = timestamp;
      const progress = Math.min((timestamp - startTime.current) / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(eased * target);

      if (progress < 1) {
        ref.current = requestAnimationFrame(animate);
      }
    };

    ref.current = requestAnimationFrame(animate);

    return () => {
      if (ref.current) cancelAnimationFrame(ref.current);
      startTime.current = null;
    };
  }, [end, duration]);

  return (
    <span>
      {prefix}{Number(value).toFixed(decimals)}{suffix}
    </span>
  );
};

export default AnimatedCounter;
