import { useCallback, useLayoutEffect, useState } from 'react';

/**
 * Measures a chart wrapper after layout so Recharts never receives width/height 0.
 * ResponsiveContainer with width="100%" can read 0×0 when mounting inside flex + overflow
 * after a route change, which triggers errors like "Cannot read properties of null (reading 'getContext')".
 */
export function useChartContainerSize(fixedHeight: number) {
  const [node, setNode] = useState<HTMLDivElement | null>(null);
  const [dimensions, setDimensions] = useState<{ width: number; height: number } | null>(null);

  const ref = useCallback((el: HTMLDivElement | null) => {
    setNode(el);
  }, []);

  useLayoutEffect(() => {
    if (!node) {
      setDimensions(null);
      return;
    }

    const update = () => {
      const w = Math.floor(node.getBoundingClientRect().width);
      const width = Math.max(1, w);
      const height = Math.max(1, fixedHeight);
      setDimensions((prev) =>
        prev && prev.width === width && prev.height === height ? prev : { width, height }
      );
    };

    update();
    const ro = new ResizeObserver(() => {
      requestAnimationFrame(update);
    });
    ro.observe(node);
    return () => ro.disconnect();
  }, [node, fixedHeight]);

  return { ref, dimensions };
}
