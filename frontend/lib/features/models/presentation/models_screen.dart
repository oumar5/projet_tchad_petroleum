import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api_error.dart';
import '../../../core/formatters.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/error_state.dart';
import '../../../core/widgets/loading_skeleton.dart';
import '../data/models_repository.dart';

final _repoProvider = Provider<ModelsRepository>(
  (ref) => ModelsRepository(ref.watch(apiClientProvider)),
);

final _modelsProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) => ref.watch(_repoProvider).list(),
);

String _qualifier(double v) {
  if (v >= 0.85) return 'Excellent';
  if (v >= 0.70) return 'Correct';
  if (v >= 0.50) return 'À améliorer';
  return 'Faible';
}

/// Business-oriented descriptor for each model_type.
class _UseCase {
  const _UseCase({
    required this.type,
    required this.title,
    required this.summary,
    required this.inputs,
    required this.output,
    required this.icon,
    required this.color,
    required this.primaryMetricKey,
    required this.primaryMetricLabel,
  });

  final String type;
  final String title;
  final String summary;
  final List<String> inputs;
  final String output;
  final IconData icon;
  final Color color;
  final String primaryMetricKey;
  final String primaryMetricLabel;

  String qualityHint(double v) => _qualifier(v);
}

const _useCases = <_UseCase>[
  _UseCase(
    type: 'maintenance',
    title: 'Maintenance prédictive',
    summary:
        'Anticipe les pannes de pompe à venir pour planifier les interventions au bon moment.',
    inputs: [
      'Production journalière d\'huile',
      'Watercut',
      'Nombre de puits actifs',
      'Tendance et moyennes mobiles 7/30 j',
    ],
    output: 'Risque de panne dans les 7 jours (faible / moyen / élevé)',
    icon: Icons.health_and_safety_rounded,
    color: AppColors.dangerRed,
    primaryMetricKey: 'accuracy',
    primaryMetricLabel: 'Précision',
  ),
  _UseCase(
    type: 'forecast',
    title: 'Prévision de production',
    summary:
        'Projette la production d\'huile journalière sur 7 à 90 jours pour aider à la planification.',
    inputs: [
      'Historique de production (lag 1, 7 et 14 jours)',
      'Moyennes mobiles 7 et 14 jours',
      'Saisonnalité (mois, jour de semaine)',
      'Watercut et puits actifs',
    ],
    output: 'Volume d\'huile prévu par jour (bbl) avec intervalle 95 %',
    icon: Icons.timeline_rounded,
    color: AppColors.petrolDeep,
    primaryMetricKey: 'r2',
    primaryMetricLabel: 'Qualité d\'ajustement (R²)',
  ),
  _UseCase(
    type: 'water',
    title: 'Optimisation injection eau',
    summary:
        'Recommande le débit d\'injection d\'eau qui maximise le rendement huile / eau.',
    inputs: [
      'Production huile et eau',
      'Watercut et sa variation',
      'Ratio eau/huile',
      'Moyennes mobiles 7 et 30 j',
    ],
    output: 'Débit d\'injection recommandé et efficacité de balayage attendue',
    icon: Icons.water_drop_rounded,
    color: AppColors.tealAccent,
    primaryMetricKey: 'r2',
    primaryMetricLabel: 'Qualité d\'ajustement (R²)',
  ),
];

/// IA pédagogique — utilisée comme onglet dans la page Configuration.
class ModelsManagementView extends ConsumerWidget {
  const ModelsManagementView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final models = ref.watch(_modelsProvider);
    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(_modelsProvider),
      child: models.when(
        loading: () => ListView.separated(
          padding: const EdgeInsets.all(20),
          itemCount: 3,
          separatorBuilder: (_, _) => const SizedBox(height: 12),
          itemBuilder: (_, _) => const Skeleton(height: 220, radius: 16),
        ),
        error: (e, _) => ErrorState(
            error: e, onRetry: () => ref.invalidate(_modelsProvider)),
        data: (rows) => ListView(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
          children: [
            const _IntroBanner(),
            const SizedBox(height: 16),
            for (final uc in _useCases) ...[
              _UseCaseCard(
                useCase: uc,
                models: rows
                    .where((r) =>
                        (r['model_type']?.toString() ?? '') == uc.type)
                    .toList(),
                onTrain: () => _showTrainSheet(context, ref, uc),
                onActivate: (id) => _activate(context, ref, id),
              ),
              const SizedBox(height: 14),
            ],
            if (rows.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: EmptyState(
                  icon: Icons.precision_manufacturing_outlined,
                  title: 'Aucun modèle entraîné',
                  subtitle:
                      'Lance le premier entraînement depuis une carte ci-dessus.',
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _activate(BuildContext context, WidgetRef ref, String id) async {
    try {
      await ref.read(_repoProvider).activate(id);
      ref.invalidate(_modelsProvider);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Modèle activé')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(prettyError(e))),
      );
    }
  }

  void _showTrainSheet(BuildContext context, WidgetRef ref, _UseCase uc) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => _TrainSheet(useCase: uc, repoProvider: _repoProvider, modelsProvider: _modelsProvider),
    );
  }
}

class _IntroBanner extends StatelessWidget {
  const _IntroBanner();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.petrolDeep.withValues(alpha: 0.10),
            AppColors.tealAccent.withValues(alpha: 0.10),
          ],
        ),
        borderRadius: BorderRadius.circular(AppRadii.lg),
        border: Border.all(
          color: scheme.outlineVariant.withValues(alpha: 0.5),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.petrolDeep.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.auto_awesome_rounded,
                color: AppColors.petrolDeep, size: 24),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Trois modèles d\'IA au service de la production',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Chaque modèle apprend à partir de l\'historique réel des puits du Tchad. '
                  'Tu peux le réentraîner à tout moment quand de nouvelles données sont disponibles.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _UseCaseCard extends StatefulWidget {
  const _UseCaseCard({
    required this.useCase,
    required this.models,
    required this.onTrain,
    required this.onActivate,
  });
  final _UseCase useCase;
  final List<Map<String, dynamic>> models;
  final VoidCallback onTrain;
  final void Function(String modelId) onActivate;

  @override
  State<_UseCaseCard> createState() => _UseCaseCardState();
}

class _UseCaseCardState extends State<_UseCaseCard> {
  bool _showTechnical = false;

  @override
  Widget build(BuildContext context) {
    final uc = widget.useCase;
    final scheme = Theme.of(context).colorScheme;
    final activeModel = widget.models
        .where((m) => m['is_active'] == true)
        .cast<Map<String, dynamic>?>()
        .firstWhere((_) => true, orElse: () => null);

    final score = activeModel == null
        ? null
        : (((activeModel['metrics'] as Map?)?[uc.primaryMetricKey] as num?)
            ?.toDouble());

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: uc.color.withValues(alpha: 0.14),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Icon(uc.icon, size: 26, color: uc.color),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        uc.title,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w800),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        uc.summary,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            // Quality + state
            Row(
              children: [
                Expanded(
                  child: _StatusPill(
                    activeModel: activeModel,
                    color: uc.color,
                  ),
                ),
                if (score != null) ...[
                  const SizedBox(width: 12),
                  Expanded(
                    child: _ScoreCard(
                      label: uc.primaryMetricLabel,
                      value: score,
                      qualifier: uc.qualityHint(score),
                      color: uc.color,
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 18),
            _TwoColRow(
              left: _BulletList(
                title: 'Données utilisées',
                icon: Icons.data_usage_rounded,
                items: uc.inputs,
              ),
              right: _BulletList(
                title: 'Ce qu\'il prédit',
                icon: Icons.auto_graph_rounded,
                items: [uc.output],
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                FilledButton.icon(
                  onPressed: widget.onTrain,
                  icon: const Icon(Icons.fitness_center_rounded),
                  label: Text(activeModel == null
                      ? 'Entraîner'
                      : 'Réentraîner'),
                ),
                const Spacer(),
                TextButton.icon(
                  onPressed: widget.models.isEmpty
                      ? null
                      : () => setState(() => _showTechnical = !_showTechnical),
                  icon: Icon(_showTechnical
                      ? Icons.expand_less_rounded
                      : Icons.expand_more_rounded),
                  label: Text(_showTechnical
                      ? 'Masquer les détails'
                      : 'Détails techniques'),
                ),
              ],
            ),
            if (_showTechnical && widget.models.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Divider(height: 1),
              const SizedBox(height: 12),
              for (final m in widget.models)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: _TechnicalRow(
                    model: m,
                    onActivate: () => widget.onActivate(m['id'].toString()),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _TwoColRow extends StatelessWidget {
  const _TwoColRow({required this.left, required this.right});
  final Widget left;
  final Widget right;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (ctx, c) {
        if (c.maxWidth < 480) {
          return Column(children: [left, const SizedBox(height: 14), right]);
        }
        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(child: left),
            const SizedBox(width: 16),
            Expanded(child: right),
          ],
        );
      },
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.activeModel, required this.color});
  final Map<String, dynamic>? activeModel;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final isActive = activeModel != null;
    final label = isActive ? 'Modèle actif' : 'Pas encore entraîné';
    final subtitle = isActive
        ? 'Version ${activeModel!['version'] ?? '—'} · ${fmtDate(activeModel!['trained_at'])}'
        : 'Lance un entraînement pour activer.';
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isActive
            ? AppColors.goodGreen.withValues(alpha: 0.10)
            : scheme.surfaceContainerHighest.withValues(alpha: 0.4),
        borderRadius: BorderRadius.circular(AppRadii.md),
        border: Border.all(
          color: isActive
              ? AppColors.goodGreen.withValues(alpha: 0.4)
              : scheme.outlineVariant.withValues(alpha: 0.4),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isActive
                    ? Icons.check_circle_rounded
                    : Icons.pending_actions_rounded,
                color: isActive ? AppColors.goodGreen : scheme.outline,
                size: 18,
              ),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  color: isActive ? AppColors.goodGreen : scheme.onSurface,
                ),
              ),
            ],
          ),
          const SizedBox(height: 2),
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

class _ScoreCard extends StatelessWidget {
  const _ScoreCard({
    required this.label,
    required this.value,
    required this.qualifier,
    required this.color,
  });
  final String label;
  final double value;
  final String qualifier;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final pct = (value.clamp(0, 1) * 100).toStringAsFixed(0);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(AppRadii.md),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: scheme.onSurfaceVariant,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 4),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                pct,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: color,
                ),
              ),
              const SizedBox(width: 2),
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text(
                  '%',
                  style: TextStyle(
                    color: color, fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  qualifier,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    color: color,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _BulletList extends StatelessWidget {
  const _BulletList({
    required this.title,
    required this.icon,
    required this.items,
  });
  final String title;
  final IconData icon;
  final List<String> items;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 16, color: scheme.primary),
            const SizedBox(width: 6),
            Text(
              title,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                fontWeight: FontWeight.w800,
                color: scheme.primary,
                letterSpacing: 0.4,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        for (final item in items)
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.only(top: 6, right: 8),
                  child: Container(
                    width: 4, height: 4,
                    decoration: BoxDecoration(
                      color: scheme.onSurfaceVariant,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
                Expanded(
                  child: Text(
                    item,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

class _TechnicalRow extends StatelessWidget {
  const _TechnicalRow({required this.model, required this.onActivate});
  final Map<String, dynamic> model;
  final VoidCallback onActivate;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final isActive = model['is_active'] == true;
    final metrics = (model['metrics'] as Map?) ?? const {};

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest.withValues(alpha: 0.35),
        borderRadius: BorderRadius.circular(AppRadii.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    Text(
                      model['version']?.toString() ?? '—',
                      style: const TextStyle(
                        fontFamily: 'monospace',
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    Text(
                      '· ${model['algorithm'] ?? '—'}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    Text(
                      '· ${fmtDate(model['trained_at'])}',
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
                      horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.goodGreen.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: const Text(
                    'ACTIF',
                    style: TextStyle(
                      color: AppColors.goodGreen,
                      fontWeight: FontWeight.w800,
                      fontSize: 11,
                    ),
                  ),
                )
              else
                TextButton(
                  onPressed: onActivate,
                  child: const Text('Activer'),
                ),
            ],
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 4,
            children: [
              for (final entry in metrics.entries)
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: scheme.surface,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    '${entry.key}: ${_fmtMetric(entry.value)}',
                    style: const TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                      fontFamily: 'monospace',
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  String _fmtMetric(dynamic v) {
    if (v is num) {
      if (v.abs() > 100) return v.toStringAsFixed(1);
      if (v.abs() >= 1) return v.toStringAsFixed(3);
      return v.toStringAsFixed(4);
    }
    return v.toString();
  }
}

class _TrainSheet extends ConsumerStatefulWidget {
  const _TrainSheet({
    required this.useCase,
    required this.repoProvider,
    required this.modelsProvider,
  });
  final _UseCase useCase;
  final Provider<ModelsRepository> repoProvider;
  final FutureProvider<List<Map<String, dynamic>>> modelsProvider;

  @override
  ConsumerState<_TrainSheet> createState() => _TrainSheetState();
}

class _TrainSheetState extends ConsumerState<_TrainSheet> {
  String _algo = 'gradient_boosting';
  bool _submitting = false;
  String? _jobStatus;
  String? _jobError;
  DateTime? _startedAt;
  Duration _elapsed = Duration.zero;
  Timer? _ticker;

  @override
  void dispose() {
    _ticker?.cancel();
    super.dispose();
  }

  void _startTicker() {
    _ticker?.cancel();
    _startedAt = DateTime.now();
    _elapsed = Duration.zero;
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted || _startedAt == null) return;
      setState(() => _elapsed = DateTime.now().difference(_startedAt!));
    });
  }

  Future<void> _submit() async {
    setState(() {
      _submitting = true;
      _jobStatus = 'queued';
      _jobError = null;
    });
    _startTicker();
    try {
      final repo = ref.read(widget.repoProvider);
      final jobId = await repo.startTraining(
        modelType: widget.useCase.type,
        algorithm: _algo,
      );
      String finalStatus = 'queued';
      for (var i = 0; i < 100; i++) {
        await Future<void>.delayed(const Duration(seconds: 2));
        if (!mounted) return;
        final job = await repo.getJob(jobId);
        final status = job['status']?.toString() ?? 'queued';
        final err = job['error']?.toString();
        if (mounted) {
          setState(() {
            _jobStatus = status;
            _jobError = err;
          });
        }
        if (status == 'success' || status == 'failed') {
          finalStatus = status;
          break;
        }
      }
      _ticker?.cancel();
      ref.invalidate(widget.modelsProvider);
      if (!mounted) return;
      if (finalStatus == 'success') {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Entraînement terminé. Nouveau modèle activé.')),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _jobStatus = 'failed';
          _jobError = prettyError(e);
        });
      }
    } finally {
      _ticker?.cancel();
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final uc = widget.useCase;
    final scheme = Theme.of(context).colorScheme;
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
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: scheme.outlineVariant,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: uc.color.withValues(alpha: 0.14),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(uc.icon, color: uc.color),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Entraîner « ${uc.title} »',
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w800),
                      ),
                      Text(
                        uc.summary,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: scheme.surfaceContainerHighest.withValues(alpha: 0.4),
                borderRadius: BorderRadius.circular(AppRadii.md),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline_rounded, size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Le modèle sera entraîné sur l\'intégralité des '
                      'données disponibles, puis activé automatiquement '
                      'à la fin si l\'apprentissage réussit.',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: _algo,
              decoration: const InputDecoration(
                labelText: 'Algorithme',
                helperText:
                    'Gradient Boosting est recommandé pour la plupart des cas.',
                prefixIcon: Icon(Icons.psychology_alt_rounded),
              ),
              items: const [
                DropdownMenuItem(
                    value: 'gradient_boosting',
                    child: Text('Gradient Boosting (recommandé)')),
                DropdownMenuItem(
                    value: 'random_forest',
                    child: Text('Random Forest (plus rapide)')),
                DropdownMenuItem(
                    value: 'xgboost',
                    child: Text('XGBoost (plus précis, plus lent)')),
              ],
              onChanged: _submitting
                  ? null
                  : (v) => setState(() => _algo = v ?? 'gradient_boosting'),
            ),
            const SizedBox(height: 20),
            if (_submitting || _jobStatus == 'failed')
              _TrainProgress(
                status: _jobStatus ?? 'queued',
                error: _jobError,
                elapsed: _elapsed,
                color: uc.color,
              )
            else
              FilledButton.icon(
                onPressed: _submit,
                icon: const Icon(Icons.fitness_center_rounded),
                label: const Text('Démarrer l\'entraînement'),
              ),
            const SizedBox(height: 8),
            if (!_submitting && _jobStatus != 'failed')
              Text(
                'L\'entraînement prend généralement entre 5 et 30 secondes.',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
              ),
            if (_jobStatus == 'failed') ...[
              const SizedBox(height: 12),
              FilledButton.tonalIcon(
                onPressed: _submit,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Réessayer'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Visual feedback during ML training: stepper + indeterminate progress + elapsed time + error.
class _TrainProgress extends StatelessWidget {
  const _TrainProgress({
    required this.status,
    required this.elapsed,
    required this.color,
    this.error,
  });

  final String status;
  final Duration elapsed;
  final Color color;
  final String? error;

  static const _steps = [
    ('queued', 'En file d\'attente', Icons.hourglass_empty_rounded),
    ('running', 'Entraînement en cours', Icons.psychology_rounded),
    ('success', 'Modèle activé', Icons.check_circle_rounded),
  ];

  int get _currentIndex {
    if (status == 'failed') return 1;
    if (status == 'success') return 2;
    if (status == 'running') return 1;
    return 0;
  }

  String _frenchStatus() {
    switch (status) {
      case 'queued':
        return 'Préparation des données…';
      case 'running':
        return 'Apprentissage en cours sur l\'historique…';
      case 'success':
        return 'Terminé avec succès';
      case 'failed':
        return 'Échec';
      default:
        return status;
    }
  }

  String _formatElapsed() {
    final s = elapsed.inSeconds;
    if (s < 60) return '${s}s';
    return '${s ~/ 60}m ${s % 60}s';
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final isFailed = status == 'failed';
    final accent = isFailed ? scheme.error : color;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(AppRadii.md),
        border: Border.all(color: accent.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              for (int i = 0; i < _steps.length; i++) ...[
                _StepDot(
                  label: _steps[i].$2,
                  icon: _steps[i].$3,
                  state: i < _currentIndex
                      ? _StepState.done
                      : (i == _currentIndex
                          ? (isFailed ? _StepState.failed : _StepState.active)
                          : _StepState.pending),
                  color: accent,
                ),
                if (i < _steps.length - 1)
                  Expanded(
                    child: Container(
                      height: 2,
                      margin: const EdgeInsets.symmetric(horizontal: 4),
                      color: i < _currentIndex
                          ? accent
                          : scheme.outlineVariant.withValues(alpha: 0.5),
                    ),
                  ),
              ],
            ],
          ),
          const SizedBox(height: 14),
          if (!isFailed)
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                minHeight: 6,
                color: accent,
                backgroundColor: accent.withValues(alpha: 0.15),
                value: status == 'success' ? 1 : null,
              ),
            ),
          const SizedBox(height: 12),
          Row(
            children: [
              Icon(
                isFailed
                    ? Icons.error_outline_rounded
                    : Icons.timer_outlined,
                size: 16,
                color: accent,
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  _frenchStatus(),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: accent,
                  ),
                ),
              ),
              if (!isFailed)
                Text(
                  _formatElapsed(),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontFamily: 'monospace',
                    color: scheme.onSurfaceVariant,
                  ),
                ),
            ],
          ),
          if (isFailed && error != null) ...[
            const SizedBox(height: 6),
            Text(
              error!,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: scheme.onSurfaceVariant,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

enum _StepState { pending, active, done, failed }

class _StepDot extends StatelessWidget {
  const _StepDot({
    required this.label,
    required this.icon,
    required this.state,
    required this.color,
  });
  final String label;
  final IconData icon;
  final _StepState state;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final (bg, fg, ic) = switch (state) {
      _StepState.done => (color, Colors.white, Icons.check_rounded),
      _StepState.active => (color.withValues(alpha: 0.15), color, icon),
      _StepState.failed => (scheme.errorContainer, scheme.error, Icons.close_rounded),
      _StepState.pending => (
          scheme.surfaceContainerHighest.withValues(alpha: 0.5),
          scheme.outline,
          icon,
        ),
    };
    return Tooltip(
      message: label,
      child: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(color: bg, shape: BoxShape.circle),
        alignment: Alignment.center,
        child: state == _StepState.active
            ? SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2.5, color: fg),
              )
            : Icon(ic, size: 18, color: fg),
      ),
    );
  }
}
