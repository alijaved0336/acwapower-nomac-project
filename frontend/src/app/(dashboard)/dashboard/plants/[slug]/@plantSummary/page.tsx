import { Suspense } from "react";

import { Skeleton } from "antd";
import PlantSummary from "@/components/features/dashboard/Plant/PlantSummary";

const Page = async () => {
  return (
    <Suspense fallback={<Skeleton />}>
      <PlantSummary />
    </Suspense>
  );
};

export default Page;
