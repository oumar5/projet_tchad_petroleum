import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api_error.dart';
import '../../../core/formatters.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/kpi_card.dart';
import '../../../core/widgets/section_header.dart';

class WaterScreen extends ConsumerStatefulWidget {
  const WaterScreen({super.key});

  @override
  ConsumerState<WaterScreen> createState() => _WaterScreenState();
}

class _WaterScreenState extends ConsumerState<WaterScreen> {
  final _blockCtrl = TextEditingController(text: 'X');
  final _targetCtrl = TextEditingController();
  Map<String, dynamic>? _result;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _blockCtrl.dispose();
    _targetCtrl.dispose();
    super.dispose();
  }

  Future<void> _run() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      final r = await api.dio.post('/v1/ml/predict/water', data: {
        'block': _blockCtrl.text,
        'target_oil_bbl': _targetCtrl.text.isEmpty
            ? null
            : double.tryParse(_targetCtrl.text),
      });
      setState(() => _result = Map<String, dynamic>.from(r.data as Map));
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
                  TextField(
                    controller: _blockCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Bloc',
                      prefixIcon: Icon(Icons.layers_rounded),
                    ),
                  ),
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

    final injection = first['recommended_injection_bbl'] as num?;
    final expectedOil = first['expected_oil_bbl'] as num?;
    final swept = first['sweep_efficiency_pct'] as num?;
    final block = (first['block'] ?? '—').toString();
    final confidence = (result['confidence'] as num?)?.toDouble();
    final modelMap = result['model'];
    final modelName = modelMap is Map
        ? '${modelMap['name'] ?? '—'} v${modelMap['version'] ?? '?'}'
        : '—';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: 'Recommandation pour le bloc $block',
          subtitle: 'Modèle : $modelName',
        ),
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
                    label: 'Injection recommandée',
                    value: fmtBbl(injection),
                    icon: Icons.water_drop_rounded,
                    iconColor: AppColors.tealAccent,
                  ),
                ),
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
                    value: swept == null ? '—' : fmtPct(swept),
                    icon: Icons.speed_rounded,
                    iconColor: AppColors.goldAmber,
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
                  const Icon(Icons.verified_rounded,
                      color: AppColors.goodGreen),
                  const SizedBox(width: 10),
                  Text(
                    'Confiance du modèle : ',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  Text(
                    '${(confidence * 100).toStringAsFixed(0)} %',
                    style: const TextStyle(fontWeight: FontWeight.w800),
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
