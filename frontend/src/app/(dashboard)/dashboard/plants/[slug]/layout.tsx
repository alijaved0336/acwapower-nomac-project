import { Flex } from "antd";

import type { FC, PropsWithChildren, ReactNode } from "react";
import PlantHeader from "@/components/features/dashboard/Plant/PlantHeader";

interface IProps {
  plantSummary: ReactNode;
  plantEquipmentKpi: ReactNode;
}
const Layout: FC<PropsWithChildren<IProps>> = (props) => {
  return (
    <Flex vertical gap={24}>
      <PlantHeader />
      {props.plantSummary}
      {props.plantEquipmentKpi}
    </Flex>
  );
};

export default Layout;
