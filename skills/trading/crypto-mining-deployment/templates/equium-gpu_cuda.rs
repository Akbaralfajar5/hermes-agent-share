//! CUDA-based leaf generator for Equihash 96,5.
//!
//! Replaces the wgpu implementation which segfaults on NVIDIA Vulkan drivers.
//! Calls the `eqm-leaves` CUDA binary as a subprocess.
//! Falls back to CPU blake2b if the binary is not found or fails.
//!
//! GPU selection: reads EQM_GPU_ID env var (default 0).
//! Run 4 instances with EQM_GPU_ID=0/1/2/3 for 4-GPU setup.

use anyhow::{anyhow, Result};
use std::process::Command;

/// Equihash 96,5 leaf size in bytes (n / 8).
pub const LEAF_BYTES: usize = 12;

/// 60-byte BLAKE2b output → 5 leaves per call.
pub const LEAVES_PER_CALL: u32 = 5;

pub struct GpuLeafGen {
    pub backend: String,
    pub adapter_name: String,
    binary_path: String,
    gpu_id: u32,
}

impl GpuLeafGen {
    pub fn new() -> Result<Self> {
        // Read GPU ID from env var EQM_GPU_ID (default 0)
        let gpu_id: u32 = std::env::var("EQM_GPU_ID")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(0);
        Self::new_with_gpu(gpu_id)
    }

    pub fn new_with_gpu(gpu_id: u32) -> Result<Self> {
        let candidates = vec![
            std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(|d| d.join("eqm-leaves")))
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_default(),
            "/root/equium/eqm-leaves".to_string(),
            "./eqm-leaves".to_string(),
        ];

        let mut found = None;
        for path in &candidates {
            if !path.is_empty() && std::path::Path::new(path).exists() {
                found = Some(path.clone());
                break;
            }
        }

        let binary_path = found.ok_or_else(|| {
            anyhow!("eqm-leaves CUDA binary not found. Searched: {:?}", candidates)
        })?;

        // Smoke test on the target GPU
        let test_input = "ab".repeat(81);
        let test_nonce = "cd".repeat(32);
        let out = Command::new(&binary_path)
            .args([&test_input, &test_nonce, "5", &gpu_id.to_string()])
            .output()
            .map_err(|e| anyhow!("eqm-leaves smoke test failed: {e}"))?;

        if !out.status.success() {
            return Err(anyhow!(
                "eqm-leaves GPU{gpu_id} smoke test failed: {}",
                String::from_utf8_lossy(&out.stderr)
            ));
        }

        Ok(Self {
            backend: "CUDA".to_string(),
            adapter_name: format!("NVIDIA CUDA GPU{gpu_id} (eqm-leaves binary)"),
            binary_path,
            gpu_id,
        })
    }

    /// Generate `n_leaves` leaves into `out` using the CUDA binary.
    pub fn generate(&self, input: &[u8; 81], nonce: &[u8; 32], _n_leaves: u32, out: &mut [u8]) -> Result<()> {
        let input_hex = hex::encode(input);
        let nonce_hex = hex::encode(nonce);
        let n_leaves = 131072u32; // always full Equihash width

        let result = Command::new(&self.binary_path)
            .args([&input_hex, &nonce_hex, &n_leaves.to_string(), &self.gpu_id.to_string()])
            .output()
            .map_err(|e| anyhow!("eqm-leaves exec failed: {e}"))?;

        if !result.status.success() {
            return Err(anyhow!(
                "eqm-leaves failed: {}",
                String::from_utf8_lossy(&result.stderr)
            ));
        }

        let hex_out = String::from_utf8_lossy(&result.stdout);
        let hex_out = hex_out.trim();
        let expected_hex_len = n_leaves as usize * LEAF_BYTES * 2;

        if hex_out.len() < expected_hex_len {
            return Err(anyhow!(
                "eqm-leaves output too short: got {} hex chars, expected {}",
                hex_out.len(), expected_hex_len
            ));
        }

        let bytes = hex::decode(&hex_out[..expected_hex_len])
            .map_err(|e| anyhow!("eqm-leaves hex decode failed: {e}"))?;

        out[..n_leaves as usize * LEAF_BYTES].copy_from_slice(&bytes);
        Ok(())
    }
}
