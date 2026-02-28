import React from "react";
import {
  AbsoluteFill,
  Img,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { FadeIn } from "../components/FadeIn";
import { SlideUp } from "../components/SlideUp";

export type ServiceHeroProps = {
  sceneImageUrl: string;
  headline: string;
  subtext?: string;
  ctaText?: string;
  brandName?: string;
  accentColor?: string;
};

export const ServiceHero: React.FC<ServiceHeroProps> = ({
  sceneImageUrl,
  headline,
  subtext,
  ctaText,
  brandName,
  accentColor = "#FFFFFF",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // --- Timeline (30fps, 240 frames total) ---
  // 0-30:    Scene photo fades in from black
  // 30-90:   Gradient scrim animates in, brand name fades in
  // 90-150:  Headline slides up
  // 150-195: Subtext fades in
  // 195-240: CTA scales in, hold to end

  // Scene photo fade-in (0-30 frames = 0-1s)
  const sceneOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Gradient scrim (30-70 frames = 1-2.3s)
  const scrimOpacity = interpolate(frame, [30, 70], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // CTA scale-in (195-220 frames = 6.5-7.3s)
  const ctaProgress = spring({
    frame: frame - 195,
    fps,
    config: { damping: 10, stiffness: 100, mass: 0.6 },
  });
  const ctaScale = interpolate(ctaProgress, [0, 1], [0.6, 1]);
  const ctaOpacity = ctaProgress;

  // CTA pulse (after 220 frames)
  const pulsePhase = frame > 220 ? Math.sin((frame - 220) * 0.15) * 0.03 : 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Scene photo */}
      <AbsoluteFill style={{ opacity: sceneOpacity }}>
        <Img
          src={sceneImageUrl}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center",
          }}
        />
      </AbsoluteFill>

      {/* Gradient scrim */}
      <AbsoluteFill
        style={{
          opacity: scrimOpacity,
          background:
            "linear-gradient(to top, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.42) 45%, rgba(0,0,0,0.12) 70%, transparent 100%)",
        }}
      />

      {/* Brand name - top left */}
      {brandName && (
        <FadeIn startFrame={40} durationFrames={25}>
          <div
            style={{
              position: "absolute",
              top: 40,
              left: 72,
              fontSize: 22,
              fontWeight: 700,
              color: accentColor,
              letterSpacing: 1,
              textTransform: "uppercase" as const,
              textShadow: "0 2px 8px rgba(0,0,0,0.5)",
              fontFamily:
                "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
            }}
          >
            {brandName}
          </div>
        </FadeIn>
      )}

      {/* Text block — bottom aligned */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-end",
          alignItems: "flex-start",
          padding: "0 72px 80px 72px",
        }}
      >
        {/* Headline */}
        <SlideUp startFrame={90} offsetPx={60}>
          <div
            style={{
              fontSize: 62,
              fontWeight: 800,
              lineHeight: 1.15,
              color: "#FFFFFF",
              letterSpacing: -1,
              textShadow: "0 2px 16px rgba(0,0,0,0.6)",
              marginBottom: 20,
              maxWidth: 900,
              whiteSpace: "pre-line",
              fontFamily:
                "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
            }}
          >
            {headline}
          </div>
        </SlideUp>

        {/* Subtext */}
        {subtext && (
          <FadeIn startFrame={150} durationFrames={25}>
            <div
              style={{
                fontSize: 24,
                fontWeight: 400,
                lineHeight: 1.5,
                color: "rgba(255,255,255,0.85)",
                textShadow: "0 1px 8px rgba(0,0,0,0.5)",
                marginBottom: 32,
                maxWidth: 750,
                fontFamily:
                  "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
              }}
            >
              {subtext}
            </div>
          </FadeIn>
        )}

        {/* CTA button */}
        {ctaText && (
          <div
            style={{
              opacity: ctaOpacity,
              transform: `scale(${ctaScale + pulsePhase})`,
            }}
          >
            <div
              style={{
                display: "inline-block",
                padding: "16px 40px",
                background: accentColor,
                color: "#000000",
                fontSize: 20,
                fontWeight: 700,
                borderRadius: 6,
                letterSpacing: 0.5,
                fontFamily:
                  "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
              }}
            >
              {ctaText}
            </div>
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
