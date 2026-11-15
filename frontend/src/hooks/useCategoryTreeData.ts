import { useMemo, useState, useCallback } from "react";
import { PumpTreeNode } from "@/components/common/TreeView/types";

interface PumpCategory {
  id: string;
  name: string;
}

interface UseCategoryTreeDataProps {
  categories: PumpCategory[];
  onCategorySelect?: (categoryId: string) => void;
}

export const useCategoryTreeData = ({
  categories,
  onCategorySelect,
}: UseCategoryTreeDataProps) => {
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  const [selectedKeys, setSelectedKeys] = useState<React.Key[]>([]);
  const [searchValue, setSearchValue] = useState<string>("");

  // Transform categories into tree structure (flat, no children)
  const treeData = useMemo<PumpTreeNode[]>(() => {
    if (!categories || categories.length === 0) return [];

    return categories.map((category) => ({
      key: category.id,
      title: category.name,
      iconType: "folder" as const,
      isLeaf: true,
      metadata: {
        type: "category" as const,
        categoryKey: category.id,
      },
    }));
  }, [categories]);

  // Filter tree data based on search
  const filteredTreeData = useMemo<PumpTreeNode[]>(() => {
    if (!searchValue.trim()) return treeData;

    return treeData.filter((node) =>
      node.title.toLowerCase().includes(searchValue.toLowerCase())
    );
  }, [treeData, searchValue]);

  const handleExpand = useCallback((keys: React.Key[]) => {
    setExpandedKeys(keys);
  }, []);

  const handleSelect = useCallback(
    (keys: React.Key[], info: any) => {
      setSelectedKeys(keys);

      if (keys.length > 0 && info.node?.metadata) {
        const metadata = info.node.metadata;
        if (metadata.type === "category" && metadata.categoryKey) {
          onCategorySelect?.(metadata.categoryKey);
        }
      }
    },
    [onCategorySelect]
  );

  const handleSearch = useCallback((value: string) => {
    setSearchValue(value);
  }, []);

  // Set initial selection
  const setInitialSelection = useCallback((categoryId: string) => {
    setSelectedKeys([categoryId]);
  }, []);

  return {
    treeData: filteredTreeData,
    selectedKeys,
    expandedKeys,
    searchValue,
    handleExpand,
    handleSelect,
    handleSearch,
    setInitialSelection,
  };
};
