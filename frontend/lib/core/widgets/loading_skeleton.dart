import 'package:flutter/material.dart';

class Skeleton extends StatefulWidget {
  const Skeleton({
    super.key,
    this.width,
    this.height = 16,
    this.radius = 6,
  });

  final double? width;
  final double height;
  final double radius;

  @override
  State<Skeleton> createState() => _SkeletonState();
}

class _SkeletonState extends State<Skeleton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1100),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (_, _) {
        return Container(
          width: widget.width,
          height: widget.height,
          decoration: BoxDecoration(
            color: Color.lerp(
              scheme.surfaceContainerHighest,
              scheme.surfaceContainerHigh,
              _ctrl.value,
            ),
            borderRadius: BorderRadius.circular(widget.radius),
          ),
        );
      },
    );
  }
}

class KpiSkeleton extends StatelessWidget {
  const KpiSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 200,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Theme.of(context).colorScheme.outlineVariant.withValues(
                alpha: 0.4,
              ),
        ),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Skeleton(width: 110, height: 12),
          SizedBox(height: 16),
          Skeleton(width: 140, height: 24),
          SizedBox(height: 8),
          Skeleton(width: 60, height: 14),
        ],
      ),
    );
  }
}
