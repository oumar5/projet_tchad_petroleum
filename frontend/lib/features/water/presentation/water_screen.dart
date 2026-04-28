import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api_error.dart';
import '../../../core/formatters.dart';
import '../../../core/providers.dart';
import '../../../core/providers/blocks_providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/kpi_card.dart';
import '../../../core/widgets/section_header.dart';
import '../../../core/widgets/zone_block_picker.dart';
import '../data/water_repository.dart';

final _repoProvider = Provider<WaterRepository>(
  (ref) => WaterRepository(ref.watch(apiClientProvider)),
);

class WaterScreen extends ConsumerStatefulWidget {
  const WaterScreen({super.key});

  @override
  ConsumerState<WaterScreen> createState() => _WaterScreenState();
}

class _WaterScreenState extends ConsumerState<WaterScreen> {
  final _targetCtrl = TextEditingController();
  Map<String, dynamic>? _result;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _targetCtrl.dispose();
    super.dispose();
  }

  Future<void> _run() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final block = ref.read(selectedBlockProvider);
      final r = await ref.read(_repoProvider).recommend(
            block: block,
            targetOilBbl: _targetCtrl.text.isEmpty
                ? null
                : double.tryParse(_targetCtrl.text),
          );
      setState(() => _result = r);
    } catch (e) {
      setState(() => _error = prettyError(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Optimisation injection eau')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Paramètres',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 16),
                  const ZoneBlockPicker(),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _targetCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Production cible (bbl, optionnel)',
                      prefixIcon: Icon(Icons.flag_rounded),
                    ),
                    keyboardType: TextInputType.number,
                  ),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: _loading ? null : _run,
                    icon: _loading
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.calculate_rounded),
                    label: Text(_loading
                        ? 'Calcul en cours…'
                        : 'Calculer la recommandation'),
                  ),
                ],
              ),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Card(
              color: scheme.errorContainer.withValues(alpha: 0.6),
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    Icon(Icons.error_outline, color: scheme.error),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        _error!,
                        style: TextStyle(
                          color: scheme.onErrorContainer,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: 20),
          if (_result == null && _error == null && !_loading)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 40),
              child: EmptyState(
                icon: Icons.water_drop_rounded,
                title: 'Aucune recommandation calculée',
                subtitle:
                    'Renseigne le bloc et la cible pour obtenir un débit optimisé.',
              ),
            )
          else if (_result != null)
            _WaterResult(result: _result!),
        ],
      ),
    );
  }
}

class _WaterResult extends StatelessWidget {
  const _WaterResult({required this.result});
  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final preds = result['predictions'];
    final first = preds is List && preds.isNotEmpty
        ? Map<String, dynamic>.from(preds.first as Map)
        : <String, dynamic>{};

    final cur = (first['current_injection_bbl'] as num?)?.toDouble() ?? 0;
    final reco = (first['recommended_injection_bbl'] as num?)?.toDouble() ?? 0;
    final delta = reco - cur;
    final deltaPct = cur == 0 ? 0.0 : (delta / cur) * 100;
    final expectedOil = (first['expected_oil_bbl'] as num?)?.toDouble();
    final sweep = (first['sweep_efficiency_pct'] as num?)?.toDouble();
    final baselineEff = (first['baseline_efficiency'] as num?)?.toDouble();

    final block = (first['block'] ?? '—').toString();
    final modelMap = result['model'];
    final modelName = modelMap is Map
        ? '${modelMap['name'] ?? '—'} ${modelMap['version'] ?? ''}'
        : '—';
    final algo = modelMap is Map ? (modelMap['algorithm'] ?? '—').toString() : '—';
    final confidence = (result['confidence'] as num?)?.toDouble();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: 'Recommandation pour le bloc $block',
          subtitle: 'Modèle : $modelName · $algo',
        ),
        // Before / After comparison
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: LayoutBuilder(
              builder: (ctx, c) {
                final stack = c.maxWidth < 520;
                final left = _BeforeAfterCard(
                  label: 'Injection actuelle',
                  value: fmtBbl(cur),
                  subtitle: 'Débit moyen récent',
                  icon: Icons.opacity_rounded,
                  color: AppColors.warnOrange,
                );
                final right = _BeforeAfterCard(
                  label: 'Injection recommandée',
                  value: fmtBbl(reco),
                  subtitle: delta >= 0
                      ? '+${fmtBbl(delta.abs())} (${deltaPct.toStringAsFixed(1)} %)'
                      : '−${fmtBbl(delta.abs())} (${deltaPct.toStringAsFixed(1)} %)',
                  icon: Icons.water_drop_rounded,
                  color: delta < 0 ? AppColors.goodGreen : AppColors.tealAccent,
                  highlight: true,
                );
                if (stack) {
                  return Column(children: [
                    left,
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 12),
                      child: Icon(Icons.arrow_downward_rounded,
                          color: AppColors.tealAccent),
                    ),
                    right,
                  ]);
                }
                return Row(children: [
                  Expanded(child: left),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 12),
                    child: Icon(Icons.arrow_forward_rounded,
                        color: AppColors.tealAccent),
                  ),
                  Expanded(child: right),
                ]);
              },
            ),
          ),
        ),
        const SizedBox(height: 16),
        const SectionHeader(title: 'Indicateurs détaillés'),
        LayoutBuilder(
          builder: (ctx, c) {
            final w = c.maxWidth < 540 ? c.maxWidth : (c.maxWidth - 24) / 3;
            return Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                SizedBox(
                  width: w,
                  child: KpiCard(
                    label: 'Huile attendue',
                    value: fmtBbl(expectedOil),
                    icon: Icons.oil_barrel_rounded,
                    iconColor: AppColors.petrolDeep,
                  ),
                ),
                SizedBox(
                  width: w,
                  child: KpiCard(
                    label: 'Efficacité de balayage',
                    value: sweep == null ? '—' : fmtPct(sweep),
                    icon: Icons.speed_rounded,
                    iconColor: AppColors.goldAmber,
                  ),
                ),
                SizedBox(
                  width: w,
                  child: KpiCard(
                    label: 'Efficacité baseline',
                    value: baselineEff == null
                        ? '—'
                        : '${(baselineEff * 100).toStringAsFixed(1)} %',
                    icon: Icons.straighten_rounded,
                    iconColor: AppColors.tealAccent,
                  ),
                ),
              ],
            );
          },
        ),
        if (confidence != null) ...[
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Icon(
                    confidence >= 0.7
                        ? Icons.verified_rounded
                        : Icons.help_outline_rounded,
                    color: confidence >= 0.7
                        ? AppColors.goodGreen
                        : AppColors.warnOrange,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Confiance du modèle : '
                      '${(confidence * 100).toStringAsFixed(0)} %',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _BeforeAfterCard extends StatelessWidget {
  const _BeforeAfterCard({
    required this.label,
    required this.value,
    required this.subtitle,
    required this.icon,
    required this.color,
    this.highlight = false,
  });
  final String label;
  final String value;
  final String subtitle;
  final IconData icon;
  final Color color;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: highlight
            ? color.withValues(alpha: 0.10)
            : scheme.surfaceContainerHighest.withValues(alpha: 0.4),
        borderRadius: BorderRadius.circular(AppRadii.md),
        border: Border.all(
          color: highlight
              ? color.withValues(alpha: 0.4)
              : scheme.outlineVariant.withValues(alpha: 0.4),
          width: highlight ? 1.5 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  label,
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    color: scheme.onSurfaceVariant,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w800,
              color: highlight ? color : null,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            subtitle,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: scheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}
