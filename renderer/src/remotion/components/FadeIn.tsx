import type React from "react";
import { useCurrentFrame, interpolate } from "remotion";

type FadeInProps = {
  startFrame: number;
  durationFrames?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
};

export const FadeIn: React.FC<FadeInProps> = ({
  startFrame,
  durationFrames = 20,
  children,
  style,
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(
    frame,
    [startFrame, startFrame + durationFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return <div style={{ opacity, ...style }}>{children}</div>;
};
