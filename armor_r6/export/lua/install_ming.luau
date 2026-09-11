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
    ["brigandine"] = "Torso",
    ["brigandine_rivets"] = "Torso",
    ["fauld_back_0"] = "Torso",
    ["fauld_back_1"] = "Torso",
    ["fauld_front_0"] = "Torso",
    ["fauld_front_1"] = "Torso",
    ["fauld_front_2"] = "Torso",
    ["gauntlet_L"] = "Left Arm",
    ["gauntlet_R"] = "Right Arm",
    ["greave_L"] = "Left Leg",
    ["greave_R"] = "Right Leg",
    ["ming_brim"] = "Head",
    ["ming_skull"] = "Head",
    ["ming_spike"] = "Head",
    ["sabaton_L"] = "Left Leg",
    ["sabaton_R"] = "Right Leg",
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
