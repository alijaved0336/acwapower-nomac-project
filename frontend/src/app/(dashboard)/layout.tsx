import type { FC, PropsWithChildren } from "react";
import { DashboardLayout } from "@/components/layouts/DashboardLayout";

const Layout: FC<PropsWithChildren> = (props) => {
  return <DashboardLayout>{props.children}</DashboardLayout>;
};

export default Layout;
