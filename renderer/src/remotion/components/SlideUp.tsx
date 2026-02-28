import type React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";

type SlideUpProps = {
  startFrame: number;
  offsetPx?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
};

export const SlideUp: React.FC<SlideUpProps> = ({
  startFrame,
  offsetPx = 60,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - startFrame,
    fps,
    config: { damping: 14, stiffness: 120, mass: 0.8 },
  });

  const translateY = (1 - progress) * offsetPx;
  const opacity = progress;

  return (
    <div
      style={{
        transform: `translateY(${translateY}px)`,
        opacity,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
