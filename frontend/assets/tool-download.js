(function () {
  const NAMESPACE = "CanIEdit";
  const BASE_PATH = "/tools/shared/download.html";
  const SAFE_PATTERN = /^[\w.-]+$/;

  const globalObject = (typeof window !== "undefined" && window) || {};
  const registry = (globalObject[NAMESPACE] = globalObject[NAMESPACE] || {});

  function redirectToDownload(toolKey, fileId) {
    if (!toolKey) {
      throw new Error("redirectToDownload requires a tool key");
    }
    if (!fileId) {
      throw new Error("redirectToDownload requires a file identifier");
    }

    const trimmedTool = String(toolKey).trim();
    const trimmedFile = String(fileId).trim();

    if (!SAFE_PATTERN.test(trimmedFile)) {
      throw new Error("File identifier contains unsupported characters");
    }

    const query = new URLSearchParams({ tool: trimmedTool, file: trimmedFile });
    window.location.href = `${BASE_PATH}?${query.toString()}`;
  }

  registry.redirectToDownload = redirectToDownload;
})();
