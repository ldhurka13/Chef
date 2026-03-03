import React from "react";
import { motion, AnimatePresence } from "framer-motion";

const ShutterFlash = ({ show }) => {
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.1 }}
          className="fixed inset-0 bg-white z-[200] pointer-events-none"
          aria-hidden="true"
        />
      )}
    </AnimatePresence>
  );
};

export default ShutterFlash;
