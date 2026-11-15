// utils/dateHelpers.ts - Helper to format dates for API
export const formatDateForAPI = (dateString: string): string => {
  // If date is already in YYYY-MM-DD format, return as is
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    return dateString;
  }

  // If date includes time, extract just the date part
  if (dateString.includes("T") || dateString.includes(" ")) {
    return dateString.split("T")[0].split(" ")[0];
  }

  // Try to parse and format
  try {
    const date = new Date(dateString);
    if (!isNaN(date.getTime())) {
      return date.toISOString().split("T")[0];
    }
  } catch (error) {
    console.warn("Invalid date format:", dateString);
  }

  return dateString;
};
