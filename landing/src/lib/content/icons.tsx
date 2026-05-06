import {
  Bot,
  Briefcase,
  Cpu,
  Hammer,
  Home,
  MessageSquare,
  Package,
  Rocket,
  Watch,
  Wrench,
  Zap,
  Heart,
  Star,
  Box,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

export const ICON_REGISTRY: Record<string, LucideIcon> = {
  Bot,
  Briefcase,
  Cpu,
  Hammer,
  Home,
  MessageSquare,
  Package,
  Rocket,
  Watch,
  Wrench,
  Zap,
  Heart,
  Star,
  Box,
  Sparkles,
};

export const ICON_NAMES = Object.keys(ICON_REGISTRY);

export function resolveIcon(name: string, fallback: LucideIcon = Box): LucideIcon {
  return ICON_REGISTRY[name] ?? fallback;
}
