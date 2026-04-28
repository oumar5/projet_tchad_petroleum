import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api_error.dart';
import '../../../core/formatters.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/error_state.dart';
import '../../../core/widgets/loading_skeleton.dart';
import '../../../core/widgets/section_header.dart';
import '../data/models_repository.dart';

final _repoProvider = Provider<ModelsRepository>(
  (ref) => ModelsRepository(ref.watch(apiClientProvider)),
);

final _modelsProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) => ref.watch(_repoProvider).list(),
);

class ModelsScreen extends ConsumerWidget {
  const ModelsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final models = ref.watch(_modelsProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Modèles ML'),
        actions: [
          IconButton(
            tooltip: 'Actualiser',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => ref.invalidate(_modelsProvider),
          ),
          const SizedBox(width: 4),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showTrainSheet(context, ref),
        icon: const Icon(Icons.fitness_center_rounded),
        label: const Text('Entraîner'),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(_modelsProvider),
        child: models.when(
          loading: () => ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: 4,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (_, _) => const Skeleton(height: 110, radius: 16),
          ),
          error: (e, _) =>
              ErrorState(error: e, onRetry: () => ref.invalidate(_modelsProvider)),
          data: (rows) {
            if (rows.isEmpty) {
              return EmptyState(
                icon: Icons.precision_manufacturing_outlined,
                title: 'Aucun modèle entraîné',
                subtitle: 'Lance un entraînement avec le bouton ci-dessous.',
                action: FilledButton.icon(
                  onPressed: () => _showTrainSheet(context, ref),
                  icon: const Icon(Icons.fitness_center_rounded),
                  label: const Text('Démarrer un entraînement'),
                ),
              );
            }
            // Group by model_type
            final byType = <String, List<Map<String, dynamic>>>{};
            for (final r in rows) {
              final t = (r['model_type'] ?? 'autre').toString();
              byType.putIfAbsent(t, () => []).add(r);
            }
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
              children: [
                for (final entry in byType.entries) ...[
                  SectionHeader(
                    title: _typeLabel(entry.key),
                    subtitle: '${entry.value.length} version(s)',
                  ),
                  ...entry.value.map((r) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: _ModelCard(
                          row: r,
                          onActivate: () async {
                            try {
                              await ref
                                  .read(_repoProvider)
                                  .activate(r['id'].toString());
                              ref.invalidate(_modelsProvider);
                              if (!context.mounted) return;
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('Modèle activé'),
                                ),
                              );
                            } catch (e) {
                              if (!context.mounted) return;
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text(prettyError(e))),
                              );
                            }
                          },
                        ),
                      )),
                  const SizedBox(height: 8),
                ],
              ],
            );
          },
        ),
      ),
    );
  }

  String _typeLabel(String t) => switch (t) {
        'maintenance' => 'Maintenance prédictive',
        'forecast' => 'Prévision de production',
        'water' || 'water_injection' => 'Optimisation injection eau',
        _ => t,
      };

  void _showTrainSheet(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => const _TrainSheet(),
    );
  }
}

class _ModelCard extends StatelessWidget {
  const _ModelCard({required this.row, required this.onActivate});
  final Map<String, dynamic> row;
  final VoidCallback onActivate;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final isActive = row['is_active'] == true;
    final metrics = (row['metrics'] as Map?) ?? const {};
    final algo = row['algorithm']?.toString() ?? '—';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            row['name']?.toString() ?? '—',
                            style: Theme.of(context).textTheme.titleSmall
                                ?.copyWith(fontWeight: FontWeight.w700),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: scheme.surfaceContainerHighest,
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              row['version']?.toString() ?? '',
                              style: const TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                        ],
                      ),
                      Text(
                        '$algo · entraîné ${fmtDate(row['trained_at'])}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                if (isActive)
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.goodGreen.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.check_circle_rounded,
                            size: 14, color: AppColors.goodGreen),
                        SizedBox(width: 4),
                        Text(
                          'ACTIF',
                          style: TextStyle(
                            color: AppColors.goodGreen,
                            fontWeight: FontWeight.w800,
                            fontSize: 11,
                            letterSpacing: 0.6,
                          ),
                        ),
                      ],
                    ),
                  )
                else
                  TextButton(
                    onPressed: onActivate,
                    child: const Text('Activer'),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 10,
              runSpacing: 6,
              children: [
                for (final entry in metrics.entries)
                  _MetricChip(
                    label: entry.key.toString(),
                    value: _fmtMetric(entry.value),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _fmtMetric(dynamic v) {
    if (v is num) {
      final abs = v.abs();
      if (abs > 100) return v.toStringAsFixed(1);
      if (abs >= 1) return v.toStringAsFixed(3);
      return v.toStringAsFixed(4);
    }
    return v.toString();
  }
}

class _MetricChip extends StatelessWidget {
  const _MetricChip({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            label.toUpperCase(),
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: scheme.onSurfaceVariant,
              letterSpacing: 0.6,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            value,
            style: const TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w700,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    );
  }
}

class _TrainSheet extends ConsumerStatefulWidget {
  const _TrainSheet();

  @override
  ConsumerState<_TrainSheet> createState() => _TrainSheetState();
}

class _TrainSheetState extends ConsumerState<_TrainSheet> {
  String _modelType = 'forecast';
  String _algo = 'gradient_boosting';
  bool _submitting = false;
  String? _jobStatus;

  Future<void> _submit() async {
    setState(() {
      _submitting = true;
      _jobStatus = null;
    });
    try {
      final repo = ref.read(_repoProvider);
      final jobId =
          await repo.startTraining(modelType: _modelType, algorithm: _algo);

      // Poll up to 5 min
      for (var i = 0; i < 100; i++) {
        await Future<void>.delayed(const Duration(seconds: 3));
        final job = await repo.getJob(jobId);
        final status = job['status']?.toString() ?? 'queued';
        if (mounted) setState(() => _jobStatus = status);
        if (status == 'success' || status == 'failed') break;
      }

      ref.invalidate(_modelsProvider);
      if (!mounted) return;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(_jobStatus == 'success'
              ? 'Entraînement terminé avec succès'
              : 'Entraînement terminé : $_jobStatus'),
        ),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(prettyError(e))),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.fromLTRB(
          20,
          20,
          20,
          20 + MediaQuery.of(context).viewInsets.bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.outlineVariant,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Démarrer un entraînement',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: _modelType,
              decoration: const InputDecoration(
                labelText: 'Type de modèle',
                prefixIcon: Icon(Icons.model_training_rounded),
              ),
              items: const [
                DropdownMenuItem(
                    value: 'forecast', child: Text('Prévision de production')),
                DropdownMenuItem(
                    value: 'maintenance', child: Text('Maintenance prédictive')),
                DropdownMenuItem(
                    value: 'water', child: Text('Optimisation injection eau')),
              ],
              onChanged: _submitting
                  ? null
                  : (v) => setState(() => _modelType = v ?? 'forecast'),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _algo,
              decoration: const InputDecoration(
                labelText: 'Algorithme',
                prefixIcon: Icon(Icons.psychology_alt_rounded),
              ),
              items: const [
                DropdownMenuItem(
                    value: 'gradient_boosting',
                    child: Text('Gradient Boosting')),
                DropdownMenuItem(
                    value: 'random_forest', child: Text('Random Forest')),
                DropdownMenuItem(value: 'xgboost', child: Text('XGBoost')),
              ],
              onChanged: _submitting
                  ? null
                  : (v) => setState(() => _algo = v ?? 'gradient_boosting'),
            ),
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: _submitting ? null : _submit,
              icon: _submitting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.fitness_center_rounded),
              label: Text(_submitting
                  ? (_jobStatus == null
                      ? 'Démarrage…'
                      : 'Statut : $_jobStatus')
                  : 'Lancer l\'entraînement'),
            ),
          ],
        ),
      ),
    );
  }
}
