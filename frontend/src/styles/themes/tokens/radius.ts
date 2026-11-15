import type { ThemeConfig } from "antd";

type CustomConfig = ThemeConfig["token"] & {
  borderRadiusXXS: number;
  borderRadiusXL: number;
  borderRadius2XL: number;
  borderRadius3XL: number;
  borderRadius4XL: number;
  borderRadiusFull: number;
};

export const radiusToken: CustomConfig = {
  borderRadiusXXS: 2,
  borderRadiusXS: 4,
  borderRadiusSM: 6,
  borderRadius: 8,
  borderRadiusLG: 10,
  borderRadiusXL: 12,
  borderRadius2XL: 16,
  borderRadius3XL: 20,
  borderRadius4XL: 24,
  borderRadiusFull: 100,
};
