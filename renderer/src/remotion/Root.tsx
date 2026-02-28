import { Composition } from "remotion";
import { ServiceHero, type ServiceHeroProps } from "./compositions/ServiceHero";
import {
  BrandedStatic,
  type BrandedStaticProps,
} from "./compositions/BrandedStatic";

const FPS = 30;
const DURATION_SEC = 8;

const serviceHeroDefaults: ServiceHeroProps = {
  sceneImageUrl:
    "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1200&h=1200&fit=crop",
  headline: "Your rights.\nOur fight.",
  subtext:
    "Experienced criminal defense attorneys with a 94% case success rate. Available 24/7.",
  ctaText: "Free Consultation",
  brandName: "Morrison & Associates",
  accentColor: "#FFFFFF",
};

const brandedStaticDefaults: BrandedStaticProps = {
  brandName: "peec.ai",
  headline: "Turn Any Landing Page\nInto Scroll-Stopping Ads",
  description:
    "AI-powered ad creative platform that scrapes your site and generates branded creatives in seconds.",
  ctaText: "Get Started Now",
  bgColor: "#0f172a",
  accentColor: "#3b82f6",
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ServiceHero"
        component={ServiceHero}
        durationInFrames={FPS * DURATION_SEC}
        fps={FPS}
        width={1080}
        height={1080}
        defaultProps={serviceHeroDefaults}
      />
      <Composition
        id="BrandedStatic"
        component={BrandedStatic}
        durationInFrames={FPS * DURATION_SEC}
        fps={FPS}
        width={1080}
        height={1080}
        defaultProps={brandedStaticDefaults}
      />
    </>
  );
};
