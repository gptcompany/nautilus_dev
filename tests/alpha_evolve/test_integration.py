"""Integration tests for Alpha-Evolve Core Infrastructure."""

from pathlib import Path


class TestPatchInsertSampleCycle:
    """T050: Test patch -> insert -> sample cycle."""

    def test_patch_insert_sample_cycle(
        self, temp_db_path: Path, sample_strategy_single_block: str
    ):
        """Full cycle: patch strategy, insert to store, sample for next mutation."""
        from scripts.alpha_evolve.patching import apply_patch, validate_syntax
        from scripts.alpha_evolve.store import FitnessMetrics, ProgramStore

        store = ProgramStore(temp_db_path)

        # 1. Start with seed strategy
        seed_id = store.insert(sample_strategy_single_block)

        # 2. Simulate mutation: patch the strategy
        diff = {
            "blocks": {"entry_logic": "if self.ema.value < bar.close:\n    self.sell()"}
        }
        mutated_code = apply_patch(sample_strategy_single_block, diff)

        # 3. Validate patched code
        valid, msg = validate_syntax(mutated_code)
        assert valid, f"Patched code is invalid: {msg}"

        # 4. Insert mutated strategy with parent reference
        mutant_id = store.insert(mutated_code, parent_id=seed_id)

        # 5. Simulate evaluation: update metrics
        metrics = FitnessMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.1,
            cagr=0.2,
            total_return=0.4,
        )
        store.update_metrics(mutant_id, metrics)

        # 6. Sample for next mutation cycle
        sampled = store.sample(strategy="elite")
        assert sampled is not None
        assert sampled.id == mutant_id  # Only evaluated strategy

        # 7. Verify lineage
        lineage = store.get_lineage(mutant_id)
        assert len(lineage) == 2
        assert lineage[0].id == mutant_id
        assert lineage[1].id == seed_id


class TestInsertUpdateTopKCycle:
    """T051: Test insert -> update_metrics -> top_k cycle."""

    def test_insert_update_topk_cycle(self, temp_db_path: Path):
        """Full cycle: insert strategies, evaluate, query top performers."""
        from scripts.alpha_evolve.store import FitnessMetrics, ProgramStore

        store = ProgramStore(temp_db_path)

        # 1. Insert multiple strategies
        strategy_ids = []
        for i in range(10):
            prog_id = store.insert(f"def strategy_{i}(): return {i}")
            strategy_ids.append(prog_id)

        # 2. Simulate evaluation: update metrics for each
        for i, prog_id in enumerate(strategy_ids):
            # Varying fitness - higher index = better
            metrics = FitnessMetrics(
                sharpe_ratio=float(i) / 10,
                calmar_ratio=float(i),  # 0, 1, 2, ..., 9
                max_drawdown=-0.1 - (0.01 * i),
                cagr=0.1 * i,
                total_return=0.2 * i,
                trade_count=10 + i,
            )
            store.update_metrics(prog_id, metrics)

        # 3. Query top 3 performers
        top = store.top_k(k=3, metric="calmar")

        assert len(top) == 3
        assert top[0].metrics.calmar_ratio == 9.0
        assert top[1].metrics.calmar_ratio == 8.0
        assert top[2].metrics.calmar_ratio == 7.0

        # 4. Verify IDs match
        assert top[0].id == strategy_ids[9]
        assert top[1].id == strategy_ids[8]
        assert top[2].id == strategy_ids[7]


class TestFullEvolutionCycle:
    """Test complete evolution simulation."""

    def test_multi_generation_evolution(
        self, temp_db_path: Path, sample_strategy_multiple_blocks: str
    ):
        """Simulate multiple generations of evolution."""
        from scripts.alpha_evolve.patching import apply_patch, extract_blocks
        from scripts.alpha_evolve.store import FitnessMetrics, ProgramStore

        store = ProgramStore(temp_db_path, population_size=10, archive_size=3)

        # Generation 0: Seed strategies
        seed_id = store.insert(sample_strategy_multiple_blocks)
        store.update_metrics(
            seed_id,
            FitnessMetrics(
                sharpe_ratio=0.5,
                calmar_ratio=1.0,
                max_drawdown=-0.15,
                cagr=0.1,
                total_return=0.2,
            ),
        )

        # Extract blocks for mutation
        blocks = extract_blocks(sample_strategy_multiple_blocks)
        assert "entry_logic" in blocks

        # Generations 1-3: Mutate and evaluate
        current_best = seed_id
        for gen in range(1, 4):
            # Get parent
            parent = store.get(current_best)
            parent_code = parent.code

            # Mutate entry logic
            diff = {
                "blocks": {
                    "entry_logic": f"if self.ema_fast.value > self.ema_slow.value + {gen}:\n    self.buy()"
                }
            }
            mutated = apply_patch(parent_code, diff)

            # Insert and evaluate
            child_id = store.insert(mutated, parent_id=current_best)
            store.update_metrics(
                child_id,
                FitnessMetrics(
                    sharpe_ratio=0.5 + gen * 0.2,
                    calmar_ratio=1.0 + gen * 0.5,  # Improving each gen
                    max_drawdown=-0.15 + gen * 0.01,
                    cagr=0.1 + gen * 0.05,
                    total_return=0.2 + gen * 0.1,
                ),
            )

            # Update best
            current_best = child_id

        # Verify evolution improved fitness
        lineage = store.get_lineage(current_best)
        assert len(lineage) == 4  # seed + 3 generations

        # Fitness should improve along lineage
        calmars = [p.metrics.calmar_ratio for p in lineage]
        assert calmars == sorted(calmars, reverse=True)  # Descending order

        # Top k should have latest generation
        top = store.top_k(k=1)
        assert top[0].id == current_best
        assert top[0].generation == 3


class TestExportVerification:
    """T052: Verify all exports in __init__.py."""

    def test_all_exports_importable(self):
        """All public APIs are importable from package root."""
        from scripts.alpha_evolve import (
            BLOCK_RE,
            EvolutionConfig,
            FitnessMetrics,
            Program,
            ProgramStore,
            apply_patch,
            extract_blocks,
            validate_syntax,
        )

        # Verify they're not None
        assert BLOCK_RE is not None
        assert apply_patch is not None
        assert extract_blocks is not None
        assert validate_syntax is not None
        assert FitnessMetrics is not None
        assert Program is not None
        assert ProgramStore is not None
        assert EvolutionConfig is not None

    def test_package_version(self):
        """Package has version string."""
        from scripts.alpha_evolve import __version__

        assert __version__ == "0.1.0"
