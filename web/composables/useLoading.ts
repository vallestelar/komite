export const useLoading = () => {
  const pendingRequests = useState<number>("komite_pending_requests", () => 0);

  const startLoading = () => {
    pendingRequests.value += 1;
  };

  const stopLoading = () => {
    pendingRequests.value = Math.max(0, pendingRequests.value - 1);
  };

  return {
    isLoading: computed(() => pendingRequests.value > 0),
    startLoading,
    stopLoading,
  };
};
