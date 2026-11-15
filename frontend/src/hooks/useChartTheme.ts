import { getChartTheme, ChartThemeColors } from "@/utils/themeChartConfig";
import { useAppSelector } from ".";

const useChartTheme = () => {
  const mode = useAppSelector((state) => state.settings.mode);
  return getChartTheme(mode === "dark");
};

export default useChartTheme;
