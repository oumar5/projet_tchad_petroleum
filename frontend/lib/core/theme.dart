import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class AppColors {
  AppColors._();
  static const petrolDeep = Color(0xFF0E5C8A);
  static const petrolMid = Color(0xFF1F77B4);
  static const petrolSoft = Color(0xFFBFE4F4);
  static const oilBlack = Color(0xFF0B0F1A);
  static const oilCharcoal = Color(0xFF14181F);
  static const sandLight = Color(0xFFFAF8F4);
  static const sandCream = Color(0xFFF5EFE6);
  static const goldAmber = Color(0xFFF7B538);
  static const tealAccent = Color(0xFF3AAFA9);
  static const goodGreen = Color(0xFF2E8B57);
  static const warnOrange = Color(0xFFE07A2B);
  static const dangerRed = Color(0xFFC0392B);
}

class AppRadii {
  AppRadii._();
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const xl = 24.0;
}

class AppSpacing {
  AppSpacing._();
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
}

ThemeData buildLightTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: AppColors.petrolDeep,
    brightness: Brightness.light,
    primary: AppColors.petrolDeep,
    secondary: AppColors.goldAmber,
    tertiary: AppColors.tealAccent,
    surface: AppColors.sandLight,
  );
  return _build(scheme, isDark: false);
}

ThemeData buildDarkTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: AppColors.petrolDeep,
    brightness: Brightness.dark,
    primary: const Color(0xFF66B7E8),
    secondary: AppColors.goldAmber,
    tertiary: AppColors.tealAccent,
    surface: AppColors.oilCharcoal,
  );
  return _build(scheme, isDark: true);
}

ThemeData _build(ColorScheme scheme, {required bool isDark}) {
  final base = ThemeData(
    colorScheme: scheme,
    useMaterial3: true,
    scaffoldBackgroundColor: isDark ? AppColors.oilBlack : AppColors.sandCream,
    visualDensity: VisualDensity.comfortable,
  );
  return base.copyWith(
    appBarTheme: AppBarTheme(
      backgroundColor: isDark ? AppColors.oilBlack : AppColors.sandLight,
      foregroundColor: scheme.onSurface,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      systemOverlayStyle: isDark
          ? SystemUiOverlayStyle.light
          : SystemUiOverlayStyle.dark,
      titleTextStyle: base.textTheme.titleLarge?.copyWith(
        fontWeight: FontWeight.w700,
        letterSpacing: -0.2,
      ),
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      surfaceTintColor: Colors.transparent,
      color: isDark ? AppColors.oilCharcoal : Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadii.lg),
        side: BorderSide(
          color: scheme.outlineVariant.withValues(alpha: 0.4),
          width: 1,
        ),
      ),
      margin: EdgeInsets.zero,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: isDark
          ? AppColors.oilCharcoal
          : Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.md),
        borderSide: BorderSide(color: scheme.outlineVariant),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.md),
        borderSide: BorderSide(color: scheme.outlineVariant),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppRadii.md),
        borderSide: BorderSide(color: scheme.primary, width: 1.6),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.md),
        ),
        textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        elevation: 0,
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.md),
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.md),
        ),
      ),
    ),
    chipTheme: ChipThemeData(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(999),
      ),
      side: BorderSide(color: scheme.outlineVariant),
      backgroundColor: scheme.surfaceContainerHighest,
      labelStyle: TextStyle(
        color: scheme.onSurface,
        fontWeight: FontWeight.w500,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
    ),
    dividerTheme: DividerThemeData(
      color: scheme.outlineVariant.withValues(alpha: 0.5),
      thickness: 1,
      space: 1,
    ),
    floatingActionButtonTheme: FloatingActionButtonThemeData(
      elevation: 4,
      backgroundColor: scheme.primary,
      foregroundColor: scheme.onPrimary,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadii.lg),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      height: 72,
      backgroundColor: isDark ? AppColors.oilCharcoal : Colors.white,
      indicatorColor: scheme.primaryContainer,
      surfaceTintColor: Colors.transparent,
      labelTextStyle: WidgetStatePropertyAll(
        TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: scheme.onSurface,
        ),
      ),
    ),
    listTileTheme: ListTileThemeData(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppRadii.md),
      ),
    ),
    textTheme: base.textTheme.copyWith(
      headlineSmall: base.textTheme.headlineSmall?.copyWith(
        fontWeight: FontWeight.w700,
        letterSpacing: -0.4,
      ),
      titleLarge: base.textTheme.titleLarge?.copyWith(
        fontWeight: FontWeight.w700,
        letterSpacing: -0.2,
      ),
      titleMedium: base.textTheme.titleMedium?.copyWith(
        fontWeight: FontWeight.w600,
      ),
      labelLarge: base.textTheme.labelLarge?.copyWith(
        fontWeight: FontWeight.w600,
      ),
    ),
  );
}
