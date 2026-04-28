import 'package:flutter/material.dart';

import '../theme.dart';

class KpiCard extends StatelessWidget {
  const KpiCard({
    super.key,
    required this.label,
    required this.value,
    this.icon,
    this.iconColor,
    this.trailing,
    this.delta,
    this.deltaPositive,
  });

  final String label;
  final String value;
  final IconData? icon;
  final Color? iconColor;
  final Widget? trailing;
  final String? delta;
  final bool? deltaPositive;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      decoration: BoxDecoration(
        color: isDark ? AppColors.oilCharcoal : Colors.white,
        borderRadius: BorderRadius.circular(AppRadii.lg),
        border: Border.all(color: scheme.outlineVariant.withValues(alpha: 0.4)),
      ),
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              if (icon != null)
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: (iconColor ?? scheme.primary).withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(AppRadii.sm),
                  ),
                  child: Icon(icon, size: 18, color: iconColor ?? scheme.primary),
                ),
              if (icon != null) const SizedBox(width: 10),
              Expanded(
                child: Text(
                  label,
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    color: scheme.onSurfaceVariant,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.2,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              ?trailing,
            ],
          ),
          const SizedBox(height: 12),
          Text(
            value,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w800,
              letterSpacing: -0.5,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          if (delta != null) ...[
            const SizedBox(height: 6),
            _DeltaChip(
              text: delta!,
              positive: deltaPositive ?? !delta!.startsWith('-'),
            ),
          ],
        ],
      ),
    );
  }
}

class _DeltaChip extends StatelessWidget {
  const _DeltaChip({required this.text, required this.positive});
  final String text;
  final bool positive;

  @override
  Widget build(BuildContext context) {
    final color = positive ? AppColors.goodGreen : AppColors.dangerRed;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            positive ? Icons.trending_up : Icons.trending_down,
            color: color,
            size: 14,
          ),
          const SizedBox(width: 4),
          Text(
            text,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w700,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}
