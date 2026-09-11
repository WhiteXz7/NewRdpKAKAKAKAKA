-- Instalador da armadura no rig R6 (gerado automaticamente).
-- 1) Importe o .obj *_roblox_baked no Roblox Studio.
-- 2) Renomeie o Model importado para 'Armor'.
-- 3) Coloque este script DENTRO do model 'Armor' (como Script).
-- 4) Ajuste CHARACTER_NAME para o nome do seu personagem R6 no Workspace.

local CHARACTER_NAME = 'SeuPersonagemR6'
local armor = script.Parent
local character = workspace:FindFirstChild(CHARACTER_NAME)
if not character then
    for _, m in ipairs(workspace:GetChildren()) do
        if m:FindFirstChildOfClass('Humanoid') and not m:FindFirstChild('ArmorInstalled') then
            character = m; break
        end
    end
end
if not character then error('Personagem R6 nao encontrado no Workspace') end

local MAPPING = {
    ["armet_bevor"] = "Head",
    ["armet_breaths"] = "Head",
    ["armet_comb"] = "Head",
    ["armet_neck"] = "Head",
    ["armet_skull"] = "Head",
    ["armet_visor_lower"] = "Head",
    ["armet_visor_upper"] = "Head",
    ["couter_v2_L"] = "Left Arm",
    ["couter_v2_R"] = "Right Arm",
    ["couter_v2_fan_L"] = "Left Arm",
    ["couter_v2_fan_R"] = "Right Arm",
    ["cuirass_back"] = "Torso",
    ["cuirass_breast"] = "Torso",
    ["cuirass_plackart"] = "Torso",
    ["cuisse_L"] = "Left Leg",
    ["cuisse_R"] = "Right Leg",
    ["fauld_v2_back_0"] = "Torso",
    ["fauld_v2_back_1"] = "Torso",
    ["fauld_v2_front_0"] = "Torso",
    ["fauld_v2_front_1"] = "Torso",
    ["fauld_v2_front_2"] = "Torso",
    ["gauntlet_v2_cuff_L"] = "Left Arm",
    ["gauntlet_v2_cuff_R"] = "Right Arm",
    ["gauntlet_v2_knuckle_L"] = "Left Arm",
    ["gauntlet_v2_knuckle_R"] = "Right Arm",
    ["gauntlet_v2_mitten_L"] = "Left Arm",
    ["gauntlet_v2_mitten_R"] = "Right Arm",
    ["gorget"] = "Torso",
    ["greave_v2_L"] = "Left Leg",
    ["greave_v2_R"] = "Right Leg",
    ["lance_rest"] = "Torso",
    ["pauldron_v2_L"] = "Torso",
    ["pauldron_v2_R"] = "Torso",
    ["pauldron_v2_lame_0_L"] = "Torso",
    ["pauldron_v2_lame_0_R"] = "Torso",
    ["pauldron_v2_lame_1_L"] = "Torso",
    ["pauldron_v2_lame_1_R"] = "Torso",
    ["pauldron_v2_lame_2_L"] = "Torso",
    ["pauldron_v2_lame_2_R"] = "Torso",
    ["pauldron_v2_lame_3_L"] = "Torso",
    ["pauldron_v2_lame_3_R"] = "Torso",
    ["poleyn_v2_L"] = "Left Leg",
    ["poleyn_v2_R"] = "Right Leg",
    ["poleyn_v2_fan_L"] = "Left Leg",
    ["poleyn_v2_fan_R"] = "Right Leg",
    ["rerebrace_L"] = "Left Arm",
    ["rerebrace_R"] = "Right Arm",
    ["rondel_L"] = "Torso",
    ["rondel_R"] = "Torso",
    ["sabaton_v2_L"] = "Left Leg",
    ["sabaton_v2_R"] = "Right Leg",
    ["stop_rib"] = "Torso",
    ["tasset_v2_L"] = "Torso",
    ["tasset_v2_R"] = "Torso",
    ["under_arm_L"] = "Left Arm",
    ["under_arm_R"] = "Right Arm",
    ["under_leg_L"] = "Left Leg",
    ["under_leg_R"] = "Right Leg",
    ["under_torso"] = "Torso",
    ["vambrace_L"] = "Left Arm",
    ["vambrace_R"] = "Right Arm",
}

for _, part in ipairs(armor:GetDescendants()) do
    if not part:IsA('BasePart') then continue end
    local targetName = MAPPING[part.Name]
    if not targetName then continue end
    local target = character:FindFirstChild(targetName)
    if not target or not target:IsA('BasePart') then continue end
    local weld = Instance.new('Weld')
    weld.Name = 'Armor_' .. part.Name
    weld.Part0 = target
    weld.Part1 = part
    weld.C0 = CFrame.new()  -- geometria ja vem no espaco local da parte
    weld.C1 = CFrame.new()
    weld.Parent = part
    part.Anchored = false
    part.CanCollide = false
end

local tag = Instance.new('BoolValue')
tag.Name = 'ArmorInstalled'
tag.Parent = character
print('Armadura instalada com sucesso!')
