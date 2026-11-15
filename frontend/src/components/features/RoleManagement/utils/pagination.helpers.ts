export interface PaginationInfo {
  startIndex: number;
  endIndex: number;
  displayText: string;
  showingText: string;
}

export const calculatePaginationInfo = (
  currentPage: number,
  totalPages: number,
  totalItems: number,
  pageSize: number
): PaginationInfo => {
  const startIndex = (currentPage - 1) * pageSize + 1;
  const endIndex = Math.min(currentPage * pageSize, totalItems);

  return {
    startIndex,
    endIndex,
    displayText: `Page ${currentPage} of ${totalPages} | Total: ${totalItems}`,
    showingText: `Showing ${startIndex}-${endIndex} of ${totalItems}`,
  };
};
