//! CUDA batch leaf generator for Equihash 96,5.
//!
//! Replaces the wgpu gpu.rs. Uses eqm-leaves-batch binary:
//! processes N nonces in one GPU call via binary stdout (binary format).
//!
//! EQM_GPU_ID env var selects which GPU this instance uses (default 0).
//! Run 4 instances with EQM_GPU_ID=0/1/2/3 for 4-GPU setup.

use anyhow::{anyhow, Result};
use std::io::Read;
use std::process::{Command, Stdio};

pub const LEAF_BYTES: usize = 12;
pub const LEAVES_PER_CALL: u32 = 5;
pub const N_LEAVES: u32 = 131072;

pub struct GpuLeafGen {
    pub backend: String,
    pub adapter_name: String,
    binary_path: String,
    gpu_id: u32,
}

impl GpuLeafGen {
    pub fn new() -> Result<Self> {
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
                .and_then(|p| p.parent().map(|d| d.join("eqm-leaves-batch")))
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_default(),
            "/root/equium/eqm-leaves-batch".to_string(),
            "./eqm-leaves-batch".to_string(),
        ];

        let mut found = None;
        for path in &candidates {
            if !path.is_empty() && std::path::Path::new(path).exists() {
                found = Some(path.clone());
                break;
            }
        }

        let binary_path = found.ok_or_else(|| {
            anyhow!("eqm-leaves-batch CUDA binary not found. Searched: {:?}", candidates)
        })?;

        // Smoke test: 1 nonce, expect N_LEAVES * LEAF_BYTES bytes
        let test_input = "ab".repeat(81);
        let test_nonce = "cd".repeat(32);
        let out = Command::new(&binary_path)
            .args([&test_input, &test_nonce, "1", &gpu_id.to_string()])
            .output()
            .map_err(|e| anyhow!("eqm-leaves-batch smoke test failed: {e}"))?;

        if !out.status.success() {
            return Err(anyhow!(
                "eqm-leaves-batch GPU{gpu_id} smoke test failed: {}",
                String::from_utf8_lossy(&out.stderr)
            ));
        }

        let expected = N_LEAVES as usize * LEAF_BYTES;
        if out.stdout.len() < expected {
            return Err(anyhow!(
                "eqm-leaves-batch smoke test: expected {} bytes, got {}",
                expected, out.stdout.len()
            ));
        }

        Ok(Self {
            backend: "CUDA".to_string(),
            adapter_name: format!("NVIDIA CUDA GPU{gpu_id} (eqm-leaves-batch)"),
            binary_path,
            gpu_id,
        })
    }

    /// Generate leaves for a batch of nonces.
    /// Returns flat Vec<u8> of n_nonces * N_LEAVES * LEAF_BYTES bytes.
    pub fn generate_batch(&self, input: &[u8; 81], nonces: &[[u8; 32]]) -> Result<Vec<u8>> {
        let n_nonces = nonces.len();
        if n_nonces == 0 {
            return Ok(vec![]);
        }

        let input_hex = hex::encode(input);
        let nonces_hex: String = nonces.iter().map(|n| hex::encode(n)).collect();

        let mut child = Command::new(&self.binary_path)
            .args([
                &input_hex,
                &nonces_hex,
                &n_nonces.to_string(),
                &self.gpu_id.to_string(),
            ])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| anyhow!("eqm-leaves-batch spawn failed: {e}"))?;

        let mut stdout = child.stdout.take().unwrap();
        let expected = n_nonces * N_LEAVES as usize * LEAF_BYTES;
        let mut buf = Vec::with_capacity(expected);
        stdout.read_to_end(&mut buf)
            .map_err(|e| anyhow!("eqm-leaves-batch read failed: {e}"))?;

        let status = child.wait().map_err(|e| anyhow!("eqm-leaves-batch wait failed: {e}"))?;
        if !status.success() {
            return Err(anyhow!("eqm-leaves-batch exited with {status}"));
        }

        if buf.len() < expected {
            return Err(anyhow!(
                "eqm-leaves-batch output too short: got {} bytes, expected {}",
                buf.len(), expected
            ));
        }

        Ok(buf)
    }

    /// Single-nonce convenience wrapper.
    pub fn generate(&self, input: &[u8; 81], nonce: &[u8; 32], _n_leaves: u32, out: &mut [u8]) -> Result<()> {
        let result = self.generate_batch(input, &[*nonce])?;
        let copy_len = (N_LEAVES as usize * LEAF_BYTES).min(out.len());
        out[..copy_len].copy_from_slice(&result[..copy_len]);
        Ok(())
    }
}
