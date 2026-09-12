import React, { useState, useRef, useCallback, useEffect } from "react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "./ui/dialog";
import { ExternalLink, Upload, FileArchive, X, Loader2, ShieldCheck } from "lucide-react";

const LETTERBOXD_URL = "https://letterboxd.com/settings/data/";
const ACCEPTED_EXT = ".zip";

const formatBytes = (bytes) => {
  if (!bytes && bytes !== 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const isZipFile = (file) => {
  if (!file) return false;
  const nameOk = file.name?.toLowerCase().endsWith(".zip");
  const typeOk = !file.type || file.type === "application/zip" || file.type === "application/x-zip-compressed";
  return nameOk && typeOk;
};

const LetterboxdImportDialog = ({ open, onOpenChange, onUpload, uploading }) => {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);
  const dropzoneRef = useRef(null);

  useEffect(() => {
    if (!open) {
      // Reset state when closed
      setFile(null);
      setError("");
      setDragOver(false);
    }
  }, [open]);

  const acceptFile = useCallback((incoming) => {
    if (!incoming) return;
    if (!isZipFile(incoming)) {
      setError("That doesn't look like a .zip file. Please upload the ZIP export from Letterboxd.");
      setFile(null);
      return;
    }
    setError("");
    setFile(incoming);
  }, []);

  const handleFileInput = (e) => {
    const f = e.target.files?.[0];
    acceptFile(f);
    // Allow re-selecting the same file later
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    const f = e.dataTransfer?.files?.[0];
    acceptFile(f);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  };

  const handleUploadClick = async () => {
    if (!file || uploading) return;
    try {
      await onUpload(file);
    } catch (err) {
      setError(err?.message || "Could not read the ZIP. Make sure it's the export directly from Letterboxd.");
    }
  };

  const openFilePicker = () => fileInputRef.current?.click();

  // Prevent Radix from closing when interacting inside the dropzone (drag/drop)
  const stopClose = (e) => {
    e.preventDefault();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!uploading) onOpenChange(v); }}>
      <DialogContent
        className="max-w-lg bg-chef-surface/95 backdrop-blur-xl border border-white/10 text-chef-platinum shadow-cinematic"
        onInteractOutside={uploading ? stopClose : undefined}
        onEscapeKeyDown={uploading ? stopClose : undefined}
        data-testid="letterboxd-import-dialog"
      >
        <DialogHeader className="text-left">
          <DialogTitle className="font-serif text-2xl tracking-tight text-chef-platinum">
            Import from Letterboxd
          </DialogTitle>
          <DialogDescription className="text-sm text-chef-muted leading-relaxed">
            Grab your personal export from Letterboxd, then upload the ZIP here. You stay in control — we never sign in on your behalf.
          </DialogDescription>
        </DialogHeader>

        {/* Instructions */}
        <ol className="space-y-2.5 text-sm text-chef-muted/90 list-decimal list-inside">
          <li>
            Open the Letterboxd data settings in a new tab.
          </li>
          <li>Sign in to Letterboxd yourself.</li>
          <li>Request and download your personal Letterboxd data export.</li>
          <li>Come back here and upload the downloaded ZIP file below.</li>
        </ol>

        <a
          href={LETTERBOXD_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
                   border border-chef-teal/30 bg-chef-teal/10 text-chef-teal text-sm font-medium
                   hover:bg-chef-teal/20 hover:border-chef-teal/50 transition-colors
                   focus:outline-none focus:ring-2 focus:ring-chef-teal/40"
          data-testid="open-letterboxd-settings-link"
        >
          Open Letterboxd data settings
          <ExternalLink className="w-3.5 h-3.5" strokeWidth={1.75} />
        </a>

        {/* Dropzone */}
        <div
          ref={dropzoneRef}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragEnter={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={openFilePicker}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              openFilePicker();
            }
          }}
          role="button"
          tabIndex={0}
          aria-label="Upload Letterboxd export ZIP. Press Enter or Space to choose a file, or drop a file here."
          className={`mt-1 rounded-lg border-2 border-dashed p-6 flex flex-col items-center justify-center gap-3
                     transition-all cursor-pointer outline-none
                     focus-visible:ring-2 focus-visible:ring-chef-teal/40
                     ${dragOver
                        ? "border-chef-teal/60 bg-chef-teal/10"
                        : "border-white/15 hover:border-chef-teal/30 hover:bg-chef-teal/5"}`}
          data-testid="letterboxd-dropzone"
        >
          <Upload className="w-7 h-7 text-chef-muted/50" strokeWidth={1.5} />
          <p className="text-sm text-chef-platinum text-center">
            Drag and drop your Letterboxd export ZIP here, or choose a file.
          </p>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); openFilePicker(); }}
            className="px-4 py-1.5 rounded-full text-xs font-medium
                     bg-white/5 border border-white/15 text-chef-platinum
                     hover:bg-white/10 hover:border-white/25 transition-colors
                     focus:outline-none focus:ring-2 focus:ring-chef-teal/40"
            data-testid="choose-zip-btn"
          >
            Choose ZIP file
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_EXT}
            onChange={handleFileInput}
            className="sr-only"
            aria-label="Letterboxd export ZIP file"
            data-testid="letterboxd-file-input"
          />
        </div>

        {/* Selected file */}
        {file && (
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-chef-teal/5 border border-chef-teal/20"
               data-testid="letterboxd-selected-file">
            <FileArchive className="w-4 h-4 text-chef-teal flex-shrink-0" strokeWidth={1.5} />
            <div className="min-w-0 flex-1">
              <p className="text-sm text-chef-platinum truncate">{file.name}</p>
              <p className="text-xs text-chef-muted">{formatBytes(file.size)}</p>
            </div>
            {!uploading && (
              <button
                type="button"
                onClick={() => { setFile(null); setError(""); }}
                className="p-1 rounded hover:bg-white/10 text-chef-muted hover:text-chef-platinum transition-colors"
                aria-label="Remove selected file"
                data-testid="remove-selected-file-btn"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div
            role="alert"
            className="text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2"
            data-testid="letterboxd-error"
          >
            {error}
          </div>
        )}

        {/* Privacy footnote */}
        <p className="flex items-start gap-2 text-xs text-chef-muted/70 leading-relaxed">
          <ShieldCheck className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-chef-teal/70" strokeWidth={1.75} />
          <span>
            You&apos;re uploading your own downloaded export directly into this app. We do not log into Letterboxd, scrape it, or fetch your data on your behalf.
          </span>
        </p>

        {/* Action */}
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            disabled={uploading}
            className="px-4 py-2 rounded-full text-sm text-chef-muted
                     hover:text-chef-platinum hover:bg-white/5 transition-colors
                     disabled:opacity-50"
            data-testid="letterboxd-cancel-btn"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleUploadClick}
            disabled={!file || uploading}
            className="inline-flex items-center gap-2 px-5 py-2 rounded-full text-sm font-medium
                     bg-chef-teal/20 border border-chef-teal/40 text-chef-teal
                     hover:bg-chef-teal/30 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors focus:outline-none focus:ring-2 focus:ring-chef-teal/40"
            data-testid="letterboxd-upload-btn"
          >
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing…
              </>
            ) : (
              <>Upload export</>
            )}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default LetterboxdImportDialog;
