import { Suspense } from "react";

import { Skeleton } from "antd";
import PlantEquipmentKpiTable from "@/components/features/dashboard/Plant/PlantEquipmentKpiTable";

interface IProps {
  searchParams: Promise<{
    segment: string;
  }>;
}

const Page = async (_props: IProps) => {
  return (
    <Suspense fallback={<Skeleton />}>
      <PlantEquipmentKpiTable />
    </Suspense>
  );
};

export default Page;
