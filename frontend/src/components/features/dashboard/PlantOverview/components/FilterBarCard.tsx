import React from "react";
import { Typography, Flex } from "antd";
import { usePlantOverviewContext } from "../context/plantOverviewContext";
import { useAppSelector } from "@/hooks";
import { getSiteDisplayName } from "../../../../../utils/siteDisplayNames";
import { extractSitesFromClusters } from "../../../../../utils/helpers";
import Select from "@/components/common/widgets/Select";

const { Title } = Typography;
interface FilterBarCardProps {
  screenName: string;
}

const FilterBarCard: React.FC<FilterBarCardProps> = ({ screenName }) => {
  const user = useAppSelector((state) => state.auth.user);
  const sites = extractSitesFromClusters(user?.role?.clusters || []);
  const plantOptions = sites.map((site) => ({
    value: site,
    label: getSiteDisplayName(site),
  }));
  const { selectedPlant, setSelectedPlant } = usePlantOverviewContext();

  return (
    <Flex justify="space-between" style={{ paddingTop: "12px" }}>
      <Title
        level={3}
        style={{
          fontFamily: "Figtree, sans-serif",
          fontWeight: 600,
          fontStyle: "normal",
          fontSize: "var(--font-size-5xl)",
          lineHeight: "30px",
          color: "var(--Light-Grey-Light-Grey-900, #101828)",
          margin: 0,
          paddingLeft: "8px",
        }}
      >
        {screenName}
      </Title>

      <div className="w-[190px]">
        <Select
          placeholder="Select Plant"
          value={selectedPlant ? selectedPlant : undefined}
          onChange={(val: string) => setSelectedPlant(val)}
          options={plantOptions}
          size="middle"
          displayKey="label"
          valueKey="value"
        />
      </div>
    </Flex>
  );
};

export default FilterBarCard;
