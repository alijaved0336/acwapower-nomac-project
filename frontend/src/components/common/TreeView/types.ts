export type TreeNodeIconType = "folder" | "folderOpen" | "tool";

export interface PumpTreeNode {
  key: string;
  title: string;
  icon?: React.ReactNode;
  iconType?: TreeNodeIconType;
  children?: PumpTreeNode[];
  isLeaf?: boolean;
  metadata?: {
    type: "site" | "category" | "pump";
    pumpId?: string;
    categoryKey?: string;
    siteKey?: string;
    pumpData?: PumpData;
  };
}

export interface PumpData {
  pump: string;
  Pump_id: string;
  Pump_Category?: string;
}

export interface TreeSelectionState {
  selectedSite?: string;
  selectedCategory?: string;
  selectedPumpId?: string;
  selectedPumpIds?: string[];
  selectedPumpCategories?: string[];
}

export interface TreeViewSidebarProps {
  treeData: PumpTreeNode[];
  selectedKeys: React.Key[];
  expandedKeys: React.Key[];
  onSelect: (selectedKeys: React.Key[], info: any) => void;
  onExpand: (expandedKeys: React.Key[]) => void;
  loading?: boolean;
  searchValue?: string;
  onSearch?: (value: string) => void;
  className?: string;
  mainSidebarWidth?: number; // Width of the main dashboard sidebar
  selectedPumpInfo?: {
    categoryName?: string;
    pumpName?: string;
  };
  multiple?: boolean;
}

export interface PumpTreeViewProps {
  treeData: PumpTreeNode[];
  selectedKeys: React.Key[];
  expandedKeys: React.Key[];
  onSelect: (selectedKeys: React.Key[], info: any) => void;
  onExpand: (expandedKeys: React.Key[]) => void;
  loading?: boolean;
  searchValue?: string;
  height?: number;
  multiple?: boolean;
}
