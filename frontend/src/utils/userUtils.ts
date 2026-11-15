/**
 * Generate initials from a user's name
 * @param name - The user's full name
 * @returns A string containing up to 2 initials
 */
export const generateInitials = (name: string): string => {
  if (!name || typeof name !== "string") {
    return "U"; // Default fallback
  }

  const nameParts = name
    .trim()
    .split(" ")
    .filter((part) => part.length > 0);

  if (nameParts.length === 0) {
    return "U"; // Default fallback
  }

  if (nameParts.length === 1) {
    // Single name: take first two characters
    return nameParts[0].substring(0, 2).toUpperCase();
  }

  // Multiple names: take first letter of first and last name
  const firstInitial = nameParts[0].charAt(0);
  const lastInitial = nameParts[nameParts.length - 1].charAt(0);

  return (firstInitial + lastInitial).toUpperCase();
};

/**
 * Check if a URL is valid and accessible
 * @param url - The image URL to validate
 * @returns boolean indicating if the URL is valid
 */
export const isValidImageUrl = (url: string | null | undefined): boolean => {
  if (!url || typeof url !== "string") {
    return false;
  }

  // Basic URL validation
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};
