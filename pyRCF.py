#!/usr/bin/python2
from __future__ import print_function
import numpy as np
import numpad as ad
import time

from mesh import Mesh
from field import Field, CellField
from ops import  div, ddt, snGrad, laplacian, grad, implicit, explicit, forget
from ops import interpolate, upwind, TVD_dual
import utils

R = 8.314462839935299
#Cp = 2.5
#M = 11.6403
#gamma = 1./(1.-R/(M*Cp))
Cp = 1006.
gamma = 1.4
Cv = Cp/gamma

mu = 2.5e-5
#mu = 0.
Pr = 0.7
alpha = mu/Pr

#case = 'tests/shockTube/'
#case = 'tests/forwardStep/'
case = 'tests/cylinder/'
mesh = Mesh(case)

t = 0
CFL = 0.2
dt = 1e-9
stepFactor = 1.2
writeInterval = 100
nSteps = 10

#initialize
p = CellField.read('p', mesh, t)
T = CellField.read('T', mesh, t)
U = CellField.read('U', mesh, t)
print()

def primitive(rho, rhoU, rhoE):
    U = rhoU/rho
    E = rhoE/rho
    e = E - 0.5*U.magSqr()
    p = (gamma-1)*rho*e
    T = e*(1./Cv)
    return U, T, p

def conservative(U, T, p):
    e = Cv*T
    rho = p/(e*(gamma-1))
    E = e + 0.5*U.magSqr()
    rhoU = rho*U
    rhoE = rho*E
    rho.name, rhoU.name, rhoE.name = 'rho', 'rhoU', 'rhoE'
    return rho, rhoU, rhoE

rho, rhoU, rhoE = conservative(U, T, p)

for timeIndex in range(1, nSteps):

    t += dt
    t = round(t, 6)
    print('Simulation Time:', t, 'Time step:', dt)

    rho0, rhoU0, rhoE0 = CellField.copy(rho), CellField.copy(rhoU), CellField.copy(rhoE)

    def timeStep(aFbyD):
        global dt
        dt = min(dt*stepFactor, CFL/np.max(aFbyD))

    def equation(rho, rhoU, rhoE):

        rhoLF, rhoRF = TVD_dual(rho)
        rhoULF, rhoURF = TVD_dual(rhoU)
        rhoELF, rhoERF = TVD_dual(rhoE)

        ULF, TLF, pLF = primitive(rhoLF, rhoULF, rhoELF)
        URF, TRF, pRF = primitive(rhoRF, rhoURF, rhoERF)
        # not needed
        U, T, p = primitive(rho, rhoU, rhoE)
        e = Cv*T

        # numerical viscosity
        cLF, cRF = (gamma*pLF/rhoLF)**0.5, (gamma*pRF/rhoRF)**0.5
        UnLF, UnRF = ULF.dotN(), URF.dotN()
        cF = (UnLF + cLF, UnRF + cLF, UnLF - cLF, UnRF - cLF)
        aF = cF[0].abs()
        for c in cF[1:]: aF = Field.max(aF, c.abs())
        aF.name = 'aF'

        # CFL based time step: sparse update?
        aF2 = Field.max((UnLF + aF).abs(), (UnRF - aF).abs())*0.5
        timeStep(ad.value(aF2.field)/mesh.deltas)

        # flux reconstruction
        rhoFlux = 0.5*(rhoLF*UnLF + rhoRF*UnRF) - 0.5*aF*(rhoRF-rhoLF)
        rhoUFlux = 0.5*(rhoULF*UnLF + rhoURF*UnRF) - 0.5*aF*(rhoURF-rhoULF)
        rhoEFlux = 0.5*((rhoELF + pLF)*UnLF + (rhoERF + pRF)*UnRF) - 0.5*aF*(rhoERF-rhoELF)
        pF = 0.5*(pLF + pRF)
        
        # viscous part
        UnF = 0.5*(UnLF + UnRF)
        UF = 0.5*(ULF + URF)
        # zeroGrad interp on boundary for div and grad, ok?
        sigmaF = mu*(snGrad(U) + interpolate(grad(UF, ghost=True).transpose()).dotN() - (2./3)*interpolate(div(UnF, ghost=True))*mesh.Normals)
        
        return [ddt(rho, rho0, dt) + div(rhoFlux),
                ddt(rhoU, rhoU0, dt) + div(rhoUFlux) + grad(pF) - div(sigmaF),
                ddt(rhoE, rhoE0, dt) + div(rhoEFlux) - (laplacian(e, alpha) + div(sigmaF.dot(UF)))]

    def boundary(rhoI, rhoUI, rhoEI):
        rhoN = Field(rho.name, mesh, rhoI)
        rhoUN = Field(rhoU.name, mesh, rhoUI)
        rhoEN = Field(rhoE.name, mesh, rhoEI)
        UN, TN, pN = primitive(rhoN, rhoUN, rhoEN)
        U.setInternalField(UN.field)
        T.setInternalField(TN.field)
        p.setInternalField(pN.field)
    
    explicit(equation, boundary, [rho, rhoU, rhoE], dt)
    forget([p, T, U])
    rho, rhoU, rhoE = conservative(U, T, p)

    if timeIndex % writeInterval == 0:
        rho.write(t)
        rhoU.write(t)
        rhoE.write(t)
        U.write(t)
        T.write(t)
        p.write(t)

    print()
   
