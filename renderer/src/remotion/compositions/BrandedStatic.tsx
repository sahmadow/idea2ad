import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { FadeIn } from "../components/FadeIn";
import { SlideUp } from "../components/SlideUp";
import { ExpandFromCenter } from "../components/ExpandFromCenter";

export type BrandedStaticProps = {
  brandName: string;
  headline: string;
  description: string;
  ctaText: string;
  bgColor?: string;
  accentColor?: string;
  textColor?: string;
  ctaBgColor?: string;
  ctaTextColor?: string;
  ctaBorderRadius?: number;
};

const FONT_FAMILY =
  "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif";

export const BrandedStatic: React.FC<BrandedStaticProps> = ({
  brandName,
  headline,
  description,
  ctaText,
  bgColor = "#0f172a",
  accentColor = "#3b82f6",
  textColor = "#FFFFFF",
  ctaBgColor,
  ctaTextColor = "#FFFFFF",
  ctaBorderRadius = 12,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const resolvedCtaBg = ctaBgColor ?? accentColor;

  // --- Timeline (30fps, 240 frames total = 8s) ---
  // 0-15:     Background fades in from black        (0-0.5s)
  // 15-45:    Accent bar slides in from left         (0.5-1.5s)
  // 45-75:    Brand name fades in                    (1.5-2.5s)
  // 75-120:   Headline slides up with spring         (2.5-4s)
  // 120-135:  Divider expands from center            (4-4.5s)
  // 135-165:  Description fades in                   (4.5-5.5s)
  // 165-210:  CTA scales in with spring              (5.5-7s)
  // 210-240:  Hold                                   (7-8s)

  // Background fade from black
  const bgOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Accent bar slide from left
  const barWidth = interpolate(frame, [15, 45], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // CTA scale-in with spring
  const ctaProgress = spring({
    frame: frame - 165,
    fps,
    config: { damping: 10, stiffness: 100, mass: 0.6 },
  });
  const ctaScale = interpolate(ctaProgress, [0, 1], [0.6, 1]);
  const ctaOpacity = ctaProgress;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Background color layer */}
      <AbsoluteFill style={{ backgroundColor: bgColor, opacity: bgOpacity }}>
        {/* Accent bar — top */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: `${barWidth}%`,
            height: 6,
            background: accentColor,
          }}
        />

        {/* Brand name — top left */}
        <FadeIn startFrame={45} durationFrames={30}>
          <div
            style={{
              position: "absolute",
              top: 48,
              left: 60,
              fontSize: 28,
              fontWeight: 700,
              color: accentColor,
              letterSpacing: -0.5,
              fontFamily: FONT_FAMILY,
            }}
          >
            {brandName}
          </div>
        </FadeIn>

        {/* Centered content */}
        <AbsoluteFill
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "0 60px",
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              textAlign: "center",
              maxWidth: 960,
            }}
          >
            {/* Headline */}
            <SlideUp startFrame={75} offsetPx={50}>
              <div
                style={{
                  fontSize: 54,
                  fontWeight: 800,
                  lineHeight: 1.15,
                  color: textColor,
                  letterSpacing: -1,
                  marginBottom: 28,
                  fontFamily: FONT_FAMILY,
                }}
              >
                {headline}
              </div>
            </SlideUp>

            {/* Divider */}
            <ExpandFromCenter startFrame={120} durationFrames={15}>
              <div
                style={{
                  width: 80,
                  height: 4,
                  background: accentColor,
                  borderRadius: 2,
                  marginBottom: 40,
                }}
              />
            </ExpandFromCenter>

            {/* Description */}
            <FadeIn startFrame={135} durationFrames={30}>
              <div
                style={{
                  fontSize: 22,
                  fontWeight: 400,
                  lineHeight: 1.5,
                  color: "#94a3b8",
                  marginBottom: 48,
                  maxWidth: 800,
                  fontFamily: FONT_FAMILY,
                }}
              >
                {description}
              </div>
            </FadeIn>

            {/* CTA button */}
            <div
              style={{
                opacity: ctaOpacity,
                transform: `scale(${ctaScale})`,
              }}
            >
              <div
                style={{
                  display: "inline-block",
                  padding: "16px 48px",
                  background: resolvedCtaBg,
                  color: ctaTextColor,
                  fontSize: 22,
                  fontWeight: 600,
                  borderRadius: ctaBorderRadius,
                  letterSpacing: 0.3,
                  fontFamily: FONT_FAMILY,
                }}
              >
                {ctaText}
              </div>
            </div>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
