import type React from "react";
import { useCurrentFrame, interpolate } from "remotion";

type ExpandFromCenterProps = {
  startFrame: number;
  durationFrames?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
};

export const ExpandFromCenter: React.FC<ExpandFromCenterProps> = ({
  startFrame,
  durationFrames = 15,
  children,
  style,
}) => {
  const frame = useCurrentFrame();

  const scaleX = interpolate(
    frame,
    [startFrame, startFrame + durationFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const opacity = interpolate(
    frame,
    [startFrame, startFrame + Math.min(durationFrames, 8)],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <div
      style={{
        transform: `scaleX(${scaleX})`,
        transformOrigin: "center",
        opacity,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
