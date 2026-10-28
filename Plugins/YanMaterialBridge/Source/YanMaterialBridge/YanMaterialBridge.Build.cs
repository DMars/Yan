using UnrealBuildTool;
public class YanMaterialBridge : ModuleRules { public YanMaterialBridge(ReadOnlyTargetRules Target) : base(Target) { PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs; PrivateDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" }); } }
