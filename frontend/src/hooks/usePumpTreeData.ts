import { useMemo, useState, useCallback } from "react";
import {
  PumpTreeNode,
  PumpData,
  TreeSelectionState,
} from "@/components/common/TreeView/types";
import { PUMP_CATEGORY_LABELS } from "@/components/features/PumpAnalysis/utils/constants";
import { formatPumpName } from "@/components/features/PumpAnalysis/utils/chartHelpers";

interface UsePumpTreeDataProps {
  siteName: string;
  pumpsData: Record<string, PumpData[]> | undefined;
  onSelectionChange?: (selection: TreeSelectionState) => void;
  multiple?: boolean;
}

export const usePumpTreeData = ({
  siteName,
  pumpsData,
  onSelectionChange,
  multiple = false,
}: UsePumpTreeDataProps) => {
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  const [selectedKeys, setSelectedKeys] = useState<React.Key[]>([]);
  const [searchValue, setSearchValue] = useState<string>("");

  // Transform pumps data into tree structure
  const treeData = useMemo<PumpTreeNode[]>(() => {
    if (!pumpsData || !siteName) return [];

    const categories = Object.keys(pumpsData);

    return categories.map((categoryKey) => {
      const pumps = pumpsData[categoryKey] || [];
      const categoryLabel =
        PUMP_CATEGORY_LABELS[categoryKey] || formatPumpName(categoryKey);

      return {
        key: `${siteName}-${categoryKey}`,
        title: categoryLabel,
        iconType: "folder" as const,
        metadata: {
          type: "category" as const,
          categoryKey,
          siteKey: siteName,
        },
        children: pumps.map((pump) => ({
          key: `${siteName}-${categoryKey}-${pump.Pump_id}`,
          title: `${formatPumpName(pump.pump)} (${pump.Pump_id})`,
          iconType: "tool" as const,
          isLeaf: true,
          metadata: {
            type: "pump" as const,
            pumpId: pump.Pump_id,
            categoryKey,
            siteKey: siteName,
            pumpData: pump,
          },
        })),
      };
    });
  }, [pumpsData, siteName]);

  // Filter tree data based on search
  const filteredTreeData = useMemo<PumpTreeNode[]>(() => {
    if (!searchValue.trim()) return treeData;

    const filterTree = (nodes: PumpTreeNode[]): PumpTreeNode[] => {
      return nodes.reduce<PumpTreeNode[]>((acc, node) => {
        const titleMatch = node.title
          .toLowerCase()
          .includes(searchValue.toLowerCase());

        if (node.children) {
          const filteredChildren = filterTree(node.children);
          if (titleMatch || filteredChildren.length > 0) {
            acc.push({
              ...node,
              children:
                filteredChildren.length > 0 ? filteredChildren : node.children,
            });
          }
        } else if (titleMatch) {
          acc.push(node);
        }

        return acc;
      }, []);
    };

    return filterTree(treeData);
  }, [treeData, searchValue]);

  // Auto-expand nodes when searching
  const autoExpandedKeys = useMemo<React.Key[]>(() => {
    if (!searchValue.trim()) return expandedKeys;

    const keys: React.Key[] = [];
    const collectKeys = (nodes: PumpTreeNode[]) => {
      nodes.forEach((node) => {
        if (node.children && node.children.length > 0) {
          keys.push(node.key);
          collectKeys(node.children);
        }
      });
    };
    collectKeys(filteredTreeData);
    return keys;
  }, [searchValue, filteredTreeData, expandedKeys]);

  const handleExpand = useCallback((keys: React.Key[]) => {
    setExpandedKeys(keys);
  }, []);

  // Helper function to find a node by key in the tree
  const findNodeByKey = useCallback(
    (key: React.Key, nodes: PumpTreeNode[]): PumpTreeNode | null => {
      for (const node of nodes) {
        if (node.key === key) {
          return node;
        }
        if (node.children) {
          const found = findNodeByKey(key, node.children);
          if (found) return found;
        }
      }
      return null;
    },
    []
  );

  const handleSelect = useCallback(
    (keys: React.Key[], info: any) => {
      if (multiple) {
        // Multi-selection mode: restrict to same category only
        const selectedPumpNodes: PumpTreeNode[] = [];
        let targetCategory: string | undefined;

        // First, find the newly clicked node from info
        const clickedNode = info.node;
        if (clickedNode?.metadata?.type === "pump") {
          targetCategory = clickedNode.metadata.categoryKey;
        }

        // Extract all pump nodes from selected keys
        keys.forEach((key) => {
          const node = findNodeByKey(key, treeData);
          if (node?.metadata?.type === "pump") {
            selectedPumpNodes.push(node);
          }
        });

        // Determine the category to filter by
        // If a pump was clicked, use its category
        // Otherwise, if we have selected pumps, use the first one's category
        const filterCategory =
          targetCategory || selectedPumpNodes[0]?.metadata?.categoryKey;

        if (filterCategory) {
          // Filter to only pumps from the same category
          const filteredPumpNodes = selectedPumpNodes.filter(
            (node) => node.metadata?.categoryKey === filterCategory
          );

          // Update selectedKeys to only include pumps from the same category
          const filteredKeys = filteredPumpNodes.map((node) => node.key);
          setSelectedKeys(filteredKeys);

          // Extract pump IDs and categories
          const pumpIds: string[] = [];
          const pumpCategories: string[] = [];
          let selectedSite: string | undefined;

          filteredPumpNodes.forEach((node) => {
            const metadata = node.metadata!;
            pumpIds.push(metadata.pumpId!);
            pumpCategories.push(metadata.categoryKey!);
            if (!selectedSite) {
              selectedSite = metadata.siteKey;
            }
          });

          if (pumpIds.length > 0) {
            const selection: TreeSelectionState = {
              selectedSite,
              selectedPumpIds: pumpIds,
              selectedPumpCategories: pumpCategories,
              // For backward compatibility, set the first pump as selectedPumpId
              selectedPumpId: pumpIds[0],
              selectedCategory: pumpCategories[0],
            };
            onSelectionChange?.(selection);
          } else {
            // No pumps selected, clear selection
            onSelectionChange?.({
              selectedSite: undefined,
              selectedPumpIds: [],
              selectedPumpCategories: [],
            });
          }
        } else {
          // No category found, just update keys (shouldn't happen in normal flow)
          setSelectedKeys(keys);
        }
      } else {
        // Single selection mode (original behavior)
        setSelectedKeys(keys);
        if (keys.length > 0 && info.node?.metadata) {
          const metadata = info.node.metadata;

          if (metadata.type === "pump") {
            const selection: TreeSelectionState = {
              selectedSite: metadata.siteKey,
              selectedCategory: metadata.categoryKey,
              selectedPumpId: metadata.pumpId,
            };
            onSelectionChange?.(selection);
          } else if (metadata.type === "category") {
            // Auto-select first pump in category
            const categoryNode = treeData.find((n) => n.key === keys[0]);
            if (categoryNode?.children && categoryNode.children.length > 0) {
              const firstPump = categoryNode.children[0];
              if (firstPump.metadata?.type === "pump") {
                const selection: TreeSelectionState = {
                  selectedSite: firstPump.metadata.siteKey,
                  selectedCategory: firstPump.metadata.categoryKey,
                  selectedPumpId: firstPump.metadata.pumpId,
                };
                setSelectedKeys([firstPump.key]);
                onSelectionChange?.(selection);
              }
            }
          }
        }
      }
    },
    [onSelectionChange, treeData, multiple, findNodeByKey]
  );

  const handleSearch = useCallback((value: string) => {
    setSearchValue(value);
  }, []);

  // Set initial selection
  const setInitialSelection = useCallback(
    (categoryKey: string, pumpId: string) => {
      const key = `${siteName}-${categoryKey}-${pumpId}`;
      setSelectedKeys([key]);
      setExpandedKeys([`${siteName}-${categoryKey}`]);
    },
    [siteName]
  );

  return {
    treeData: filteredTreeData,
    selectedKeys,
    expandedKeys: searchValue ? autoExpandedKeys : expandedKeys,
    searchValue,
    handleExpand,
    handleSelect,
    handleSearch,
    setInitialSelection,
  };
};
